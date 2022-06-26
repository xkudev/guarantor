from guarantor import crypto
from guarantor.schemas import Identity
from guarantor.schemas import IdentityEnvelope


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

        signed_identity = SignedIdentity(
            address=addr,
            document=Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not signed_identity.verify()

        signed_identity.sign(wif)

        assert signed_identity.verify()


def test_signed_identity_invalid_sig():
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

        signed_identity = SignedIdentity(
            address=addr,
            document=Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not signed_identity.verify()

        signed_identity.signature = "DEADBEEF"

        assert not signed_identity.verify()


def test_signed_identity_invalid_identity_address():
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

        signed_identity = SignedIdentity(
            address=addr,
            document=Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not signed_identity.verify()
        signed_identity.sign(wif)
        assert signed_identity.verify()

        signed_identity.document.address = "1BTF7gU1EmgasGh85ypacDvsVKg4weZMfz"
        assert not signed_identity.verify()


def test_signed_identity_invalid_address():
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

        signed_identity = SignedIdentity(
            address=addr,
            document=Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not signed_identity.verify()
        signed_identity.sign(wif)
        assert signed_identity.verify()

        signed_identity.address = "1BTF7gU1EmgasGh85ypacDvsVKg4weZMfz"
        assert not signed_identity.verify()


def test_signed_identity_invalid_document():
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

        signed_identity = SignedIdentity(
            address=addr,
            document=Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not signed_identity.verify()

        signed_identity.sign(wif)

        signed_identity.document = Identity(address=addr, info={'foo': "bar", 'bam': "baz"})

        assert not signed_identity.verify()
