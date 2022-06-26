from guarantor import crypto
from guarantor import schemas
from guarantor import app


def test_post_envelope():

    address = '1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv'

    identity_envelope = schemas.IdentityEnvelope(
        address=address,
        document=schemas.Identity(address=address, info={'foo': "bar"}),
        signature="fa1a591f57b7be304f755c237f76bfac92abe37be278bfd2dfbbd5342f2e0109",
    )

    envelope_response = app.post_envelope(identity_envelope)

    assert envelope_response.key == "0a17f9c24cdb4555494ec74d6cb6f2a24c7e19a918fc667467b1991e60417bef"
    assert envelope_response.envelope == identity_envelope
