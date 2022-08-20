import random

from kademlia.utils import digest
from kademlia.storage import ForgetfulStorage

from guarantor import schemas


def generate_node_id() -> bytes:
    return bytes(digest(random.getrandbits(255)))


def get_distance(digest_a, digest_b) -> int:
    return int(digest_a.hex(), 16) ^ int(digest_b.hex(), 16)


class ChangeStorage(ForgetfulStorage):
    def __init__(self, ttl=604800, max_entries=1000000, node_id=None):
        super().__init__(ttl=ttl)

        self.max_entries = max_entries
        self.node_id     = node_id  # needed for value metric
        assert self.node_id is not None, "Missing required node_id!"

    def __setitem__(self, key, value):

        # TODO check max value size

        # drop invalid changes
        try:
            change = schemas.loads_change(value)

            if digest(change.change_id) != key:
                print(f"INVALID KEY: {digest(key)} != {change.change_id}")
                return

        except schemas.VerificationError as e:
            print(f"INVALID CHANGE: {e}, {value}")
            return

        super().__setitem__(key, value)

    def cull(self):
        entries = []
        for key, pair in self.data.items():
            _, value = pair

            change       = schemas.loads_change(value)
            difficulty   = schemas.get_pow_difficulty(change.change_id, change.proof_of_work)
            dist_key     = get_distance(key, self.node_id)
            dist_address = get_distance(key, change.address.encode('utf-8'))
            dist_reative = min(dist_key, dist_address) / (2 ** difficulty)

            entries.append((key, dist_reative))

        entries.sort(key=lambda e: e[1])
        while len(entries) > self.max_entries:
            key, dist_reative = entries.pop()
            del self.data[key]
