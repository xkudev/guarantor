# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import typing as typ
import pathlib as pl

import pytest
from pycoin.symbols.btc import network as BTC

from guarantor import aofdb
from guarantor import crypto

FIXTURE_KEY = crypto.KeyPair(
    wif="L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp",
    addr="1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv",
)


@pytest.fixture()
def db_client(tmpdir) -> typ.Iterator[aofdb.Client]:
    yield aofdb.Client(pl.Path(tmpdir), flag="c")


def test_doc_diff():
    doc_v1  = {'title': "Hello, World!"}
    doc_v2  = {'title': "Hallo, Welt!"}
    diff_op = aofdb.doc_diff(doc_v1, doc_v2)
    assert aofdb.doc_patch([diff_op], doc_v1) == doc_v2


def test_basic(db_client: aofdb.Client):
    doc_v1 = {'title': "Hello, World!"}
    doc_v2 = {'title': "Hallo, Welt!"}

    db_doc_v1 = db_client.post(doc_v1, 'test', wif=FIXTURE_KEY.wif)
    db_doc_v2 = db_client.post(doc_v2, 'test', wif=FIXTURE_KEY.wif, prev_doc=db_doc_v1)

    assert doc_v1 == db_doc_v1.raw_document
    assert doc_v2 == db_doc_v2.raw_document

    built_doc = db_client.get(db_doc_v2.head_id)
    assert built_doc == db_doc_v2.raw_document
