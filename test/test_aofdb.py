# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import typing as typ
import pathlib as pl

from guarantor import aofdb
from pycoin.symbols.btc import network as BTC


import pytest

@pytest.fixture()
def db_client(tmpdir) -> typ.Iterator[aofdb.Client]:
    yield aofdb.Client(pl.Path(tmpdir))


def test_basic(db_client: aofdb.Client):
    pass
    # wif, right_addr = (
    #     '5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss',
    #     '1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN',
    # ),
    #     key = BTC.parse.wif(wif)
