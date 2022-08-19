import random

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


def test_get_doctype():
    model = schemas.Identity(address="moep", props={'foo': "bar"})
    assert schemas.get_doctype(model           ) == "guarantor.schemas:Identity"
    assert schemas.get_doctype(schemas.Identity) == "guarantor.schemas:Identity"


def rand_change_id() -> str:
    return hex(int(random.random() * 1000_000_000))[2:].zfill(8)


def test_revision():
    rev = schemas.increment_revision(doctype="module:Dummy", change_id=rand_change_id(), rev=None)
    for _ in range(100):
        new_rev = schemas.increment_revision(doctype="module:Dummy", change_id=rand_change_id(), rev=rev)
        assert new_rev > rev
        rev = new_rev


def test_calculate_pow():
    rand = random.Random(0)
    for difficulty in range(2, 10):
        for _ in range(10):
            change_id = hex(int(rand.random() * 1000_000_000))[2:].zfill(8)
            pow_str   = schemas.calculate_pow(change_id, difficulty)
            bits      = schemas.get_pow_difficulty(change_id, pow_str)
            assert bits >= difficulty, (bits, change_id, pow_str)
