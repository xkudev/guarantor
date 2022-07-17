# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import typing as typ
import pathlib as pl

from guarantor import aofdb
from guarantor import crypto
from pycoin.symbols.btc import network as BTC


import pytest

FIXTURE_KEY =   crypto.KeyPair(
    wif="L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp",
    addr="1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv",
)

@pytest.fixture()
def db_client(tmpdir) -> typ.Iterator[aofdb.Client]:
    yield aofdb.Client(pl.Path(tmpdir))


def test_basic(db_client: aofdb.Client):
    raw_doc = {"state": 1}
    aof_doc = db_client.update(raw_doc, wif=FIXTURE_KEY.wif)
    aof_doc = db_client.get(aof_doc['hash'])

    aof_doc['state'] = 2
    db_client.update(doc, wif=FIXTURE_KEY.wif)

