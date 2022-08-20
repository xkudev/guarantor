import random
import logging
import binascii

from kademlia.utils import digest
from kademlia.storage import ForgetfulStorage

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


class ChangeStorage(ForgetfulStorage):
    def __init__(self, ttl=604800, max_entries=1000000, node_id=None):
        super().__init__(ttl=ttl)

        self.max_entries = max_entries
        self.node_id     = node_id  # needed for value metric
        assert self.node_id is not None, "Missing required node_id!"

    def __setitem__(self, key, value):

        # drop invalid changes
        try:
            change = schemas.loads_change(value)

            if digest(change.change_id) != key:
                logger.warning(f"Change key missmatch: {digest(change.change_id)} != {key}")
                return

        except schemas.VerificationError:
            logger.warning(f"Invalid change: {value}")
            return

        super().__setitem__(key, value)

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
