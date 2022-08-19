# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import typing as typ
import pathlib as pl

import pytest

from guarantor import docdiff
from guarantor import kvstore
from guarantor import schemas

from . import fixtures

KEYPAIR = fixtures.KEYS_FIXTURES[0]


@pytest.fixture()
def db_client(tmpdir) -> typ.Iterator[kvstore.Client]:
    yield kvstore.Client(pl.Path(tmpdir), flag="c")


def test_post(db_client: kvstore.Client):
    fields = {
        'wif'    : KEYPAIR.wif,
        'doctype': schemas.get_doctype(schemas.GenericDocument),
        'opcode' : docdiff.OP_RESET,
        'opdata' : {'title': "test123"},
    }
    change_v1 = schemas.make_change(**fields)

    fields = {
        'wif'       : KEYPAIR.wif,
        'doctype'   : schemas.get_doctype(schemas.GenericDocument),
        'opcode'    : docdiff.OP_RESET,
        'opdata'    : {'title': "test12345"},
        'parent_id' : change_v1.change_id,
        'parent_rev': change_v1.rev,
    }
    change_v2 = schemas.make_change(**fields)

    db_client.post(change_v1)
    db_client.post(change_v2)

    assert db_client.get(change_v1.change_id) == change_v1
    assert db_client.get(change_v2.change_id) == change_v2

    changes = list(db_client.iter_changes(head=change_v2.change_id))
    assert changes == [change_v2, change_v1]
