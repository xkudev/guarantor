# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
# import enum
import typing as typ

import pydantic

from guarantor import crypto


class BaseEnvelope(pydantic.BaseModel):
    address  : str
    document : pydantic.BaseModel
    signature: str | None


class Identity(pydantic.BaseModel):
    address: str
    info   : dict[str, typ.Any]


class IdentityEnvelope(BaseEnvelope):
    document: Identity


def verify_base_envelope(base_envelope: BaseEnvelope) -> bool:
    if not base_envelope.signature:
        return False
    obj       = base_envelope.document.dict()
    hexdigest = crypto.deterministic_json_hash(obj)
    return crypto.verify(address=base_envelope.address, signature=base_envelope.signature, message=hexdigest)


def sign_envelope(base_envelope: BaseEnvelope, wif: str) -> BaseEnvelope:
    obj       = base_envelope.document.dict()
    hexdigest = crypto.deterministic_json_hash(obj)
    return BaseEnvelope(
        address=base_envelope.address,
        document=base_envelope.document,
        signature=crypto.sign(hexdigest, wif),
    )


def verify_identity_envelope(identity_envelope) -> bool:
    valid_sig        = verify_base_envelope(base_envelope=identity_envelope)
    matching_attress = identity_envelope.address == identity_envelope.document.address
    return matching_attress and valid_sig


class IdentityResponse(pydantic.BaseModel):
    path    : str
    identity: IdentityEnvelope


class ChatMessage(pydantic.BaseModel):
    topic : str
    iso_ts: str
    text  : str


# maybe maybe maybe
#
#
#
# class DocumentType(str, enum.Enum):
#     EVIDENCE = "evidence"
#
#
# class GenericDocument(pydantic.BaseModel):
#     pass
#
#
# class PolicyOffer(pydantic.BaseModel):
#     pass
#
#
# class PolicyContract(pydantic.BaseModel):
#     pass
#
#
# class ClaimRole(str, enum.Enum):
#     PLAINTIFF = "plaintiff"
#     DEFENDANT = "defendant"
#     JUDGE     = "judge"
#
#
# class ClaimAssociation(pydantic.BaseModel):
#     identity: Identity
#     role    : ClaimRole
#
#
# class PolicyClaim(pydantic.BaseModel):
#     pass
