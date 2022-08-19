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


class ChangeStorage(IStorage):

    def __init__(self, ttl=604800):
        """
        By default, max age is a week.
        """
        self.data = OrderedDict()
        self.ttl = ttl

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
        pass
        # TODO filter by work
        # for _, _ in self.iter_older_than(self.ttl):
        #     self.data.popitem(last=False)

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
