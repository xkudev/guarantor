import random
import hashlib

from kademlia.utils import digest

from guarantor import dht
from guarantor import schemas

WIF = "5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss"


def test_get_distance():
    ridone   = hashlib.sha1(str(random.getrandbits(255)).encode())
    ridtwo   = hashlib.sha1(str(random.getrandbits(255)).encode())
    expected = int(ridone.hexdigest(), 16) ^ int(ridtwo.hexdigest(), 16)
    distance = dht.get_distance(ridone.digest(), ridtwo.digest())
    assert distance == expected


def test_storage_cull():

    node_id = dht.generate_node_id()
    assert len(node_id) == 20

    storage = dht.ChangeStorage(max_entries=10, node_id=node_id)

    for i in range(100):
        change = schemas.make_change(
            wif=WIF,
            doctype=f"{i}",
            opcode='bar',
            opdata={},
            difficulty=i / 10,
        )
        change_data = schemas.dumps_change(change)

        storage[digest(change.change_id)] = change_data

    assert len(storage.data) == 10
