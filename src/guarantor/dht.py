import time
import random
from itertools import takewhile
import operator
from collections import OrderedDict
from abc import abstractmethod, ABC
import pydantic
from guarantor import schemas
from guarantor import crypto
from kademlia.storage import IStorage
from kademlia.utils import digest


def generate_node_id():
    return digest(random.getrandbits(255))


def get_distance(digest_a, digest_b):
    return int(digest_a.hex(), 16) ^ int(digest_b.hex(), 16)


class ChangeStorage(IStorage):

    def __init__(self, ttl=604800, max_entries=1000000, node_id=None):
        """
        By default, max age is a week.
        """
        self.data = OrderedDict()
        self.ttl = ttl

        self.max_entries = max_entries
        self.node_id = node_id  # needed for value metric
        # TODO self.cached_value_index = {}  # key -> value metric

        assert self.node_id is not None, "Missing required node_id!"

    def __setitem__(self, key, value):

        # drop invalid changes
        try:
            change = schemas.loads_change(value)
            if digest(change.change_id) != key:
                print(f"INVALID KEY: {digest(key)} != {change.change_id}")
                return
        except schemas.VerificationError as e:
            print(f"INVALID CHANGE: {e}, {value}")
            return

        # add to storage
        if key in self.data:
            del self.data[key]
        self.data[key] = (time.monotonic(), value)
        self.cull()

    def cull(self):

        # TODO cache relatve distance
        entries = []
        for key, pair in self.data.items():
            _, value = pair

            change = schemas.loads_change(value)
            difficulty = schemas.get_pow_difficulty(
                change.change_id, change.proof_of_work
            )
            dist_key = get_distance(key, self.node_id)
            dist_address = get_distance(
                key, change.address.encode('utf-8')
            )
            dist_reative = min(dist_key, dist_address) / (2 ** difficulty)

            entries.append((key, dist_reative))

        entries.sort(key=lambda e: e[1])
        while len(entries) > self.max_entries:
            key, dist_reative = entries.pop()
            del self.data[key]


    def iter_older_than(self, seconds_old):
        min_birthday = time.monotonic() - seconds_old
        zipped = self._triple_iter()
        matches = takewhile(lambda r: min_birthday >= r[1], zipped)
        return list(map(operator.itemgetter(0, 2), matches))

    def get(self, key, default=None):
        self.cull()
        if key in self.data:
            return self[key]
        return default

    def __getitem__(self, key):
        self.cull()
        return self.data[key][1]

    def __repr__(self):
        self.cull()
        return repr(self.data)

    def _triple_iter(self):
        ikeys = self.data.keys()
        ibirthday = map(operator.itemgetter(0), self.data.values())
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ibirthday, ivalues)

    def __iter__(self):
        self.cull()
        ikeys = self.data.keys()
        ivalues = map(operator.itemgetter(1), self.data.values())
        return zip(ikeys, ivalues)
