from guarantor import crypto
from guarantor import schemas

from . import fixtures


def test_signed_identity():
    for wif, right_addr in fixtures.KEYS_FIXTURES:
        addr = crypto.get_wif_address(wif)
        assert addr == right_addr

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, props={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)

        identity_envelope = schemas.sign_envelope(identity_envelope, wif)

        assert schemas.verify_identity_envelope(identity_envelope)


def test_signed_identity_invalid_sig():
    for wif, right_addr in fixtures.KEYS_FIXTURES:
        addr = crypto.get_wif_address(wif)
        assert addr == right_addr

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, props={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)

        identity_envelope.signature = "DEADBEEF"

        assert not schemas.verify_identity_envelope(identity_envelope)


def test_signed_identity_invalid_identity_address():
    for wif, right_addr in fixtures.KEYS_FIXTURES:
        addr = crypto.get_wif_address(wif)
        assert addr == right_addr

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, props={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)
        identity_envelope = schemas.sign_envelope(identity_envelope, wif)
        assert schemas.verify_identity_envelope(identity_envelope)

        identity_envelope.document.address = "1BTF7gU1EmgasGh85ypacDvsVKg4weZMfz"
        assert not schemas.verify_identity_envelope(identity_envelope)


def test_signed_identity_invalid_address():
    for wif, right_addr in fixtures.KEYS_FIXTURES:
        addr = crypto.get_wif_address(wif)
        assert addr == right_addr

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, props={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)
        identity_envelope = schemas.sign_envelope(identity_envelope, wif)
        assert schemas.verify_identity_envelope(identity_envelope)

        identity_envelope.address = "1BTF7gU1EmgasGh85ypacDvsVKg4weZMfz"
        assert not schemas.verify_identity_envelope(identity_envelope)


def test_signed_identity_invalid_document():
    for wif, right_addr in fixtures.KEYS_FIXTURES:
        addr = crypto.get_wif_address(wif)
        assert addr == right_addr

        identity_envelope = schemas.IdentityEnvelope(
            address=addr,
            document=schemas.Identity(address=addr, props={'foo': "bar"}),
            signature=None,
        )

        assert not schemas.verify_identity_envelope(identity_envelope)

        identity_envelope = schemas.sign_envelope(identity_envelope, wif)

        identity_envelope.document = schemas.Identity(address=addr, props={'foo': "bar", 'bam': "baz"})

        assert not schemas.verify_identity_envelope(identity_envelope)


def test_get_model_type():
    model = schemas.Identity(address="moep", props={'foo': "bar"})
    assert schemas.get_model_type(model           ) == "guarantor.schemas.Identity"
    assert schemas.get_model_type(schemas.Identity) == "guarantor.schemas.Identity"
