import random
import asyncio
import logging
import binascii

from kademlia.node import Node
from kademlia.utils import digest
from kademlia.network import Server
from kademlia.storage import ForgetfulStorage
from kademlia.crawling import NodeSpiderCrawl
from kademlia.protocol import KademliaProtocol

from guarantor import schemas

logger = logging.getLogger("guarantor.dht")


def generate_node_id() -> bytes:
    return bytes(digest(random.getrandbits(255)))


def bin_to_int(bits: bytes) -> int:
    return int(bits.hex(), 16)


def int_to_bin(num: int) -> bytes:
    return binascii.unhexlify(hex(num)[2:])


def get_distance(digest_a, digest_b) -> int:
    return bin_to_int(digest_a) ^ bin_to_int(digest_b)


def load_change(key: bytes, value: bytes) -> schemas.Change | None:
    try:
        change = schemas.loads_change(value)

        if digest(change.change_id) != key:

            logger.warning(f"Change key missmatch: {digest(change.change_id).hex()} != {key.hex()}")
            return None

        return change

    except schemas.VerificationError:
        logger.warning(f"Invalid change: {value.hex()}")
        return None


class GuarantorProtocol(KademliaProtocol):
    def rpc_get_changes(self, sender, nodeid, address_digest, after_key=None):
        logger.info("get changes for %i address digest", int(nodeid.hex(), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.welcome_if_new(source)
        return self.storage.get_changes(address_digest=address_digest, after_key=after_key)

    async def call_get_changes(self, node_to_ask, address_digest, after_key=None):
        address = (node_to_ask.ip, node_to_ask.port)
        result  = await self.get_changes(address, self.source_node.id, address_digest, after_key=after_key)
        return self.handle_call_response(result, node_to_ask)


class GuarantorServer(Server):

    protocol_class = GuarantorProtocol

    async def set_digest(self, dkey, value):
        result = await super().set_digest(dkey=dkey, value=value)

        # Modify the set_digest method to additionally
        # store changes close to the change.address digest.
        # This enables finding all changes for a given address.

        change = load_change(dkey, value)
        if not change:
            return result

        address_digest = digest(change.address)
        node           = Node(address_digest)

        # code below is copied verbatim from Server.set_digest

        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            logger.warning("There are no known neighbors to set key %s", dkey.hex())
            return False

        spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        nodes  = await spider.find()
        logger.info("setting '%s' on %s", dkey.hex(), list(map(str, nodes)))

        # if this node is close too, then store here as well
        biggest = max([n.distance_to(node) for n in nodes])
        if self.node.distance_to(node) < biggest:
            self.storage[dkey] = value
        results = [self.protocol.call_store(n, dkey, value) for n in nodes]
        # return true only if at least one store call succeeded
        return any(await asyncio.gather(*results)) or result


class GuarantorStorage(ForgetfulStorage):
    def __init__(self, ksize=20, ttl=604800, max_entries=1000000, node_id=None):
        super().__init__(ttl=ttl)

        self.ksize       = ksize
        self.max_entries = max_entries
        self.node_id     = node_id  # needed for value metric
        assert self.node_id is not None, "Missing required node_id!"

    def __setitem__(self, key, value):

        # drop invalid changes
        if not load_change(key, value):
            return

        super().__setitem__(key, value)

    def get_changes(self, address_digest, after_key=None):

        keys = []
        for key, pair in self.data.items():
            _, value = pair

            change = load_change(key, value)
            if not change:
                continue
            if address_digest == digest(change.address):
                keys.append(key)

        keys.sort()

        try:
            key_index = keys.index(after_key)
            return keys[key_index + 1 : key_index + 1 + self.ksize]
        except ValueError:
            return keys[: self.ksize]

    def cull(self):
        entries = []
        for key, pair in self.data.items():
            _, value = pair

            change                = schemas.loads_change(value)
            difficulty            = schemas.get_pow_difficulty(change.change_id, change.proof_of_work)
            change_address_digest = digest(change.address)
            dist_key              = get_distance(key                  , self.node_id)
            dist_address          = get_distance(change_address_digest, self.node_id)
            dist_closest          = min(dist_key, dist_address)
            dist_weighted         = dist_closest / (2 ** difficulty)

            entries.append((key, dist_weighted))

        entries.sort(key=lambda e: e[1])

        while len(entries) > self.max_entries:
            key, dist_reative = entries.pop()
            del self.data[key]
