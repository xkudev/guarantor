# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
# import enum
from guarantor import crypto
import typing as typ

import pydantic


class Signed(pydantic.BaseModel):
    address: str
    data  : pydantic.BaseModel
    signature: str | None

    def verify(self) -> bool:
        hexdigest = crypto.deterministic_json_hash(self.data)
        crypto.verify(self.address, self.signature, hexdigest)

    def sign(self, wif: str):
        hexdigest = crypto.deterministic_json_hash(self.data)
        self.signature = crypto.sign(hexdigest, wif)


class Identity(pydantic.BaseModel):
    address: str
    info  : dict[str, typ.Any]


class SignedIdentity(Signed):
    data = Identity


class IdentityResponse(pydantic.BaseModel):
    path    : str
    identity: Identity


# class DocumentType(str, enum.Enum):
#     EVIDENCE = "evidence"


# class GenericDocument(pydantic.BaseModel):
#     pass


# class PolicyOffer(pydantic.BaseModel):
#     pass


# class PolicyContract(pydantic.BaseModel):
#     pass


# class ClaimRole(str, enum.Enum):
#     PLAINTIFF = "plaintiff"
#     DEFENDANT = "defendant"
#     JUDGE     = "judge"


# class ClaimAssociation(pydantic.BaseModel):
#     identity: Identity
#     role    : ClaimRole


# class PolicyClaim(pydantic.BaseModel):
#     pass
