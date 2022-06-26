from guarantor import crypto
from guarantor import schemas


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

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)

        identity_envelope = schemas.sign_envelope(identity_envelope, wif)

        assert schemas.verify_identity_envelope(identity_envelope)


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

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)

        identity_envelope.signature = "DEADBEEF"

        assert not schemas.verify_identity_envelope(identity_envelope)


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

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)
        identity_envelope = schemas.sign_envelope(identity_envelope, wif)
        assert schemas.verify_identity_envelope(identity_envelope)

        identity_envelope.document.address = "1BTF7gU1EmgasGh85ypacDvsVKg4weZMfz"
        assert not schemas.verify_identity_envelope(identity_envelope)


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

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)
        identity_envelope = schemas.sign_envelope(identity_envelope, wif)
        assert schemas.verify_identity_envelope(identity_envelope)

        identity_envelope.address = "1BTF7gU1EmgasGh85ypacDvsVKg4weZMfz"
        assert not schemas.verify_identity_envelope(identity_envelope)


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

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, info={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)

        identity_envelope = schemas.sign_envelope(identity_envelope, wif)

        identity_envelope.document = schemas.Identity(address=addr, info={'foo': "bar", 'bam': "baz"})

        assert not schemas.verify_identity_envelope(identity_envelope)
