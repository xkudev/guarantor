from guarantor.schemas import Identity, SignedIdentity
from guarantor import crypto


def test_signed_identity():
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
        addr = crypto.get_wif_address(wif)
        assert addr == right_addr
        pubkey = "invalid"

        signed_identity = SignedIdentity(
            address=addr,
            document=Identity(pubkey=pubkey, info={"foo": "bar"}),
            signature=None,
        )

        assert not signed_identity.verify()

        signed_identity.sign(wif)

        assert signed_identity.verify()


def test_signed_identity_invalid_sig():
    pass  # TODO implement


def test_signed_identity_invalid_pubkey():
    pass  # TODO implement


def test_signed_identity_invalid_address():
    pass  # TODO implement


def test_signed_identity_invalid_document():
    pass  # TODO implement
