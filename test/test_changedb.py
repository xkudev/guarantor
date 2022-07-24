# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import typing as typ
import pathlib as pl

import pytest
from pycoin.symbols.btc import network as BTC

from guarantor import crypto
from guarantor import schemas
from guarantor import changedb

FIXTURE_KEY = crypto.KeyPair(
    wif="L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp",
    addr="1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv",
)


@pytest.fixture()
def db_client(tmpdir) -> typ.Iterator[changedb.Client]:
    yield changedb.Client(pl.Path(tmpdir), flag="c")


def test_doc_diff():
    doc_v1  = {'title': "Hello, World!"}
    doc_v2  = {'title': "Hallo, Welt!"}
    diff_op = changedb.doc_diff(doc_v1, doc_v2)
    assert changedb.doc_patch([diff_op], doc_v1) == doc_v2


def test_basic(db_client: changedb.Client):
    doc_v1 = schemas.GenericDocument(props={'title': "Hello, World!"})
    doc_v2 = schemas.GenericDocument(props={'title': "Hallo, Welt!"})

    db_ref_v1 = db_client.post(doc_v1, wif=FIXTURE_KEY.wif)
    db_ref_v2 = db_client.post(doc_v2, wif=FIXTURE_KEY.wif, prev_ref=db_ref_v1)

    assert doc_v1 == db_ref_v1.model
    assert doc_v2 == db_ref_v2.model

    out_model = db_client.get(db_ref_v2.head_id)
    assert out_model == db_ref_v2.model
