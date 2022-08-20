import random
import hashlib
import binascii

from kademlia.utils import digest

from guarantor import dht
from guarantor import crypto
from guarantor import schemas

WIF = "5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss"


def test_get_distance():
    ridone   = hashlib.sha1(str(random.getrandbits(255)).encode())
    ridtwo   = hashlib.sha1(str(random.getrandbits(255)).encode())
    expected = int(ridone.hexdigest(), 16) ^ int(ridtwo.hexdigest(), 16)
    distance = dht.get_distance(ridone.digest(), ridtwo.digest())
    assert distance == expected


def test_storage_cull_max_entries():

    node_id = dht.generate_node_id()
    assert len(node_id) == 20

    storage = dht.ChangeStorage(max_entries=10, node_id=node_id)

    for i in range(100):
        change = schemas.make_change(
            wif=WIF,
            doctype=f"{i}",
            opcode='bar',
            opdata={},
            difficulty=(i // 10) + 1,
        )
        change_data      = schemas.dumps_change(change)
        change_id_digest = digest(change.change_id)

        storage[change_id_digest] = change_data

    assert len(storage.data) == 10


def test_storage_cull_difficulty():

    # ensure change addresses all have almost zero distance
    # to node id so that only difficulty is used to filter.

    address         = crypto.get_wif_address(WIF)
    address_node_id = digest(address)

    # move some bits so distance is not zero, preventing zero math
    node_id_num     = dht.bin_to_int(address_node_id)
    node_id_num_new = node_id_num ^ (1 << 19)
    node_id         = dht.int_to_bin(node_id_num_new)

    storage = dht.ChangeStorage(max_entries=10, node_id=node_id)

    entries = []

    for i in range(100):
        change = schemas.make_change(
            wif=WIF,
            doctype=f"{i}",
            opcode='bar',
            opdata={},
            difficulty=(i // 10) + 1,
        )
        change_data      = schemas.dumps_change(change)
        change_id_digest = digest(change.change_id)

        storage[change_id_digest] = change_data

        difficulty = schemas.get_pow_difficulty(change.change_id, change.proof_of_work)
        entries.append((change_id_digest, difficulty, change_data))

    entries.sort(key=lambda e: e[1])
    entries.reverse()

    assert len(storage.data) == 10

    for count, entry in enumerate(entries):
        change_id_digest, difficulty, change_data = entry
        saved_change_data = storage.get(change_id_digest)

        if count < 10:
            assert saved_change_data is not None
        else:
            assert saved_change_data is None
