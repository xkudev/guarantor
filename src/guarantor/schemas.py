# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
# import enum
import typing as typ

import pydantic


class Identity(pydantic.BaseModel):
    pubkey: str
    info  : dict[str, typ.Any]


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
