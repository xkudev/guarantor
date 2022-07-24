# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ
import importlib

import pydantic

from guarantor import crypto

ModelId = str

BaseModel = pydantic.BaseModel


def get_datatype(model_or_type: BaseModel | type) -> str:
    if isinstance(model_or_type, BaseModel):
        model_type = model_or_type.__class__
    else:
        model_type = model_or_type

    return model_type.__module__ + ":" + model_type.__name__


_model_types: dict[str, type] = {}


def load_model_type(datatype: str) -> type:
    if datatype not in _model_types:
        module_name, class_name = datatype.split(":", 1)
        module = importlib.import_module(module_name)
        _model_types[datatype] = getattr(module, class_name)
    return _model_types[datatype]


class BaseEnvelope(BaseModel):
    # TODO head_id   : str
    # TODO prev_id   : str | None
    # TODO generation: int

    document: BaseModel

    address  : str
    signature: str | None


class GenericDocument(BaseModel):
    props: dict[str, typ.Any]


class Identity(BaseModel):
    address: str
    props  : dict[str, typ.Any]


class IdentityEnvelope(BaseEnvelope):
    document: Identity


class IdentityResponse(BaseModel):
    path    : str
    identity: IdentityEnvelope


def verify_base_envelope(base_envelope: BaseEnvelope) -> bool:
    if base_envelope.signature is None:
        return False
    else:
        obj       = base_envelope.document.dict()
        hexdigest = crypto.deterministic_json_hash(obj)
        return crypto.verify(
            address=base_envelope.address,
            signature=base_envelope.signature,
            message=hexdigest,
        )


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


class ChatMessage(BaseModel):
    topic : str
    iso_ts: str
    text  : str


# maybe maybe maybe
#
#
#
#
#
# class PolicyOffer(BaseModel):
#     pass
#
#
# class PolicyContract(BaseModel):
#     pass
#
#
# ROLE_PLAINTIFF = "plaintiff"
# ROLE_DEFENDANT = "defendant"
# ROLE_JUDGE     = "judge"
#
#
# class ClaimAssociation(BaseModel):
#     identity: Identity
#     role    : str
#
#
# class PolicyClaim(BaseModel):
#     pass
