import time
import random
from itertools import takewhile
import operator
from collections import OrderedDict
from abc import abstractmethod, ABC
import pydantic
from guarantor import crypto
from kademlia.storage import IStorage
from kademlia.utils import digest


class Change(pydantic.BaseModel):
    address: str            # affiliation
    pow_nonce: int          # for proof of work
    data: str
    change_id: str          # digest of above fields
    signature: str          # signature of change_id


def get_change_id(address: str, pow_nonce: int, data: str) -> str:
    return crypto.deterministic_json_hash({
        'address' : address,
        'pow_nonce' : pow_nonce,
        'data': data,
    })


def get_change_hash(change: Change) -> str:
    return crypto.deterministic_json_hash(change.dict())


def generate_node_id():
    return digest(random.getrandbits(255))


def create_change(wif: str, pow_nonce: int, data: str) -> Change:
    address = crypto.get_wif_address(wif)
    change_id = get_change_id(address, pow_nonce, data)
    signature = crypto.sign(change_id, wif)
    return Change(
        address=address,
        pow_nonce=pow_nonce,
        data=data,
        change_id=change_id,
        signature=signature,
    )


def validate_change(change: Change):
    expected_change_id = get_change_id(
        change.address, change.pow_nonce, change.data
    )

    assert change.change_id == expected_change_id, f"Invalid change_id {change.change_id} != {expected_change_id}"

    assert crypto.verify(change.address, change.signature, change.change_id), f"Invalid change signature for: {change.change_id}"


class ChangeStorage(IStorage):

    def __init__(self, ttl=604800):
        """
        By default, max age is a week.
        """
        self.data = OrderedDict()
        self.ttl = ttl

    def __setitem__(self, key, value):
        if key in self.data:
            del self.data[key]
        self.data[key] = (time.monotonic(), value)
        self.cull()

    def cull(self):
        pass
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
