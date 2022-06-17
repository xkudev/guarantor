import binascii

import pytest
from pycoin.symbols.btc import network as BTC

from guarantor import crypto

MULTIBIT = '''
-----BEGIN BITCOIN SIGNED MESSAGE-----
This is an example of a signed message.
-----BEGIN BITCOIN SIGNATURE-----
Version: Bitcoin-qt (1.0)
Address: 1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN
HCT1esk/TWlF/o9UNzLDANqsPXntkMErf7erIrjH5IBOZP98cNcmWmnW0GpSAi3wbr6CwpUAN4ctNn1T71UBwSc=
-----END BITCOIN SIGNATURE-----
'''


FIXTURE = {
    'positive': {
        'address': "mkRqiCnLFFsEH6ezsE1RiMxEjLRXZzWjwe",
        # "message": binascii.hexlify(b"testmessagee"),
        'message'  : "testmessagee",
        'signature': "H8wq7z8or7jGGT06ZJ0dC1+wnmRLY/fWnW2SRSRPtypaBAFJAtYhcOl+0jyjujEio91/7eFEW9tuM/WZOusSEGc=",
        'valid'    : True,
    },
    'incorrect_address': {
        'address'  : "mkRqiCnLFFsEH6ezsE2RiMxEjLRXZzWjwe",
        'message'  : binascii.hexlify(b"testmessagee"),
        'signature': "H8wq7z8or7jGGT06ZJ0dC1+wnmRLY/fWnW2SRSRPtypaBAFJAtYhcOl+0jyjujEio91/7eFEW9tuM/WZOusSEGc=",
        'valid'    : False,
    },
    'incorrect_signature': {
        'address'  : "mkRqiCnLFFsEH6ezsE1RiMxEjLRXZzWjwe",
        'message'  : binascii.hexlify(b"testmessagee"),
        'signature': "H8wq7z8or7jGGT06ZJ1dC1+wnmRLY/fWnW2SRSRPtypaBAFJAtYhcOl+0jyjujEio91/7eFEW9tuM/WZOusSEGc=",
        'valid'    : False,
    },
    'incorrect_data': {
        'address'  : "mkRqiCnLFFsEH6ezsE1RiMxEjLRXZzWjwe",
        'message'  : binascii.hexlify(b"testmessagee"),
        'signature': "H8wq7z8or7jGGT06ZJ0dC1+wnmRLY/fWnW2SRSRPtypaBAFJAtYhcOl+0jyjujEio91/7eFEW9tuM/WZOusSEGc=",
        'valid'    : False,
    },
}


def test_pycoin():
    for wif, right_addr in [
        (
            'L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp',
            '1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv',
        ),
        (
            '5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss',
            '1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN',
        ),
    ]:
        key = BTC.parse.wif(wif)
        assert key.address() == right_addr

        vk2 = BTC.parse.address(right_addr)
        assert vk2.address() == right_addr

        for i in range(1, 30, 10):
            msg = f"test message {'A' * i}"
            sig = BTC.msg.sign(key, msg, verbose=1)
            assert right_addr in sig

            # check parsing works
            parsed_msg, parsed_addr, parsed_sig = BTC.msg.parse_signed(sig)
            assert parsed_msg  == msg       , parsed_msg
            assert parsed_addr == right_addr, parsed_addr

            sig2 = BTC.msg.sign(key, msg, verbose=0)
            assert sig2 in sig, (sig, sig2)

            assert parsed_sig == sig2, parsed_sig

            assert BTC.msg.verify(key, sig2, msg)

            assert BTC.msg.verify(key, sig2.encode('ascii'), msg)


def test_sign():
    for wif, right_addr in [
        (
            'L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp',
            '1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv',
        ),
        (
            '5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss',
            '1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN',
        ),
    ]:
        key  = BTC.parse.wif(wif)
        addr = crypto.get_address(wif)
        assert addr == right_addr
        for i in range(1, 30, 10):
            msg = f"test message {'A' * i}"
            sig = crypto.sign(msg, wif)
            assert BTC.msg.verify(key, sig, msg)


def test_verify():
    message, address, signature = BTC.msg.parse_signed(MULTIBIT)
    assert message   == "This is an example of a signed message."
    assert address   == '1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN'
    assert signature == (
        "HCT1esk/TWlF/o9UNzLDANqsPXntkMErf7erIrjH5IBOZ"
        "P98cNcmWmnW0GpSAi3wbr6CwpUAN4ctNn1T71UBwSc="
    )
    assert crypto.verify(address, signature, message)


def test_compatibility():
    for wif, right_addr in [
        (
            'L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp',
            '1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv',
        ),
        (
            '5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss',
            '1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN',
        ),
    ]:
        for i in range(1, 30, 10):
            msg  = f"test message {'A' * i}"
            sig  = crypto.sign(msg, wif)
            addr = crypto.get_address(wif)
            assert addr == right_addr
            assert crypto.verify(right_addr, sig, msg)


def __test_fixtures():
    # cleanup tests and ensure compatibility with bitcoind, etc
    address   = FIXTURE['positive']['address']
    message   = FIXTURE['positive']['message']
    signature = FIXTURE['positive']['signature']
    assert crypto.verify(address, signature, message)


def test_validate_address():
    crypto.validate_address("1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv")

    with pytest.raises(ValueError, match=r"Invalid BTC address: foo"):
        crypto.validate_address("foo")


def test_validate_wif():
    crypto.validate_wif("5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss")

    with pytest.raises(ValueError, match=r"Invalid WIF: foo"):
        crypto.validate_wif("foo")


def test_deterministic_hash():
    assert (
        crypto.deterministic_hash("foo")
        == "b2213295d564916f89a6a42455567c87c3f480fcd7a1c15e220f17d7169a790b"
    )
    assert (
        crypto.deterministic_hash(None)
        == "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b"
    )
    assert (
        crypto.deterministic_hash({'a': 'foo', 'b': 'bar'})
        == "d695d9c070d88814ac7364ba48d2aa387abe1238c760c06e8cd359758cc0d16a"
    )
    assert (
        crypto.deterministic_hash({'b': 'bar', 'a': 'foo'})
        == "d695d9c070d88814ac7364ba48d2aa387abe1238c760c06e8cd359758cc0d16a"
    )
