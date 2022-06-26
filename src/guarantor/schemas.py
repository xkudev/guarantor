# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
# import enum
import typing as typ

import pydantic

from guarantor import crypto


class BaseEvelope(pydantic.BaseModel):
    address  : str
    document : pydantic.BaseModel
    signature: str | None

    def verify(self) -> bool:
        if not self.signature:
            return False
        obj       = self.document.dict()
        hexdigest = crypto.deterministic_json_hash(obj)
        return crypto.verify(self.address, self.signature, hexdigest)

    def sign(self, wif: str) -> str:
        obj            = self.document.dict()
        hexdigest      = crypto.deterministic_json_hash(obj)
        self.signature = crypto.sign(hexdigest, wif)
        return self.signature


class Identity(pydantic.BaseModel):
    address: str
    info   : dict[str, typ.Any]


class SignedIdentity(SignedDocument):
    document: Identity

    def verify(self) -> bool:
        valid_sig        = super().verify()
        matching_attress = self.address == self.document.address
        return matching_attress and valid_sig


class IdentityResponse(pydantic.BaseModel):
    path    : str
    identity: SignedIdentity


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
