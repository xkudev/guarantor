import binascii
from guarantor import crypto
from pycoin.symbols.btc import network as BTC


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
    "positive": {
        "address": "mkRqiCnLFFsEH6ezsE1RiMxEjLRXZzWjwe",
        # "message": binascii.hexlify(b"testmessagee"),
        "message": "testmessagee",
        "signature": "H8wq7z8or7jGGT06ZJ0dC1+wnmRLY/fWnW2SRSRPtypaBAFJAtYhcOl+0jyjujEio91/7eFEW9tuM/WZOusSEGc=",
        "valid": True,
    },
    "incorrect_address": {
        "address": "mkRqiCnLFFsEH6ezsE2RiMxEjLRXZzWjwe",
        "message": binascii.hexlify(b"testmessagee"),
        "signature": "H8wq7z8or7jGGT06ZJ0dC1+wnmRLY/fWnW2SRSRPtypaBAFJAtYhcOl+0jyjujEio91/7eFEW9tuM/WZOusSEGc=",
        "valid": False,
    },
    "incorrect_signature": {
        "address": "mkRqiCnLFFsEH6ezsE1RiMxEjLRXZzWjwe",
        "message": binascii.hexlify(b"testmessagee"),
        "signature": "H8wq7z8or7jGGT06ZJ1dC1+wnmRLY/fWnW2SRSRPtypaBAFJAtYhcOl+0jyjujEio91/7eFEW9tuM/WZOusSEGc=",
        "valid": False,
    },
    "incorrect_data": {
        "address": "mkRqiCnLFFsEH6ezsE1RiMxEjLRXZzWjwe",
        "message": binascii.hexlify(b"testmessagee"),
        "signature": "H8wq7z8or7jGGT06ZJ0dC1+wnmRLY/fWnW2SRSRPtypaBAFJAtYhcOl+0jyjujEio91/7eFEW9tuM/WZOusSEGc=",
        "valid": False,
    }
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
            assert parsed_msg == msg, parsed_msg
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
        key = BTC.parse.wif(wif)
        for i in range(1, 30, 10):
            msg = f"test message {'A' * i}"
            sig = crypto.sign(msg, wif)
            assert BTC.msg.verify(key, sig, msg)


def test_verify():
    message, address, signature = BTC.msg.parse_signed(MULTIBIT)
    assert message == 'This is an example of a signed message.'
    assert address == '1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN'
    assert signature == (
        'HCT1esk/TWlF/o9UNzLDANqsPXntkMErf7erIrjH5IBOZ'
        'P98cNcmWmnW0GpSAi3wbr6CwpUAN4ctNn1T71UBwSc='
    )
    assert crypto.verify(address, signature, message)


def test_compatibility():
    message = FIXTURE["positive"]["address"]
    address = FIXTURE["positive"]["message"]
    signature = FIXTURE["positive"]["signature"]
    assert crypto.verify(address, signature, message)
