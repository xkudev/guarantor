# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import json
import typing as typ
import importlib

import pydantic
import datetime as dt

from guarantor import crypto

ChangeId = str

BaseDocument = pydantic.BaseModel
DocTypeClass = typ.Type[BaseDocument]

DocType  = typ.NewType('DocType', str)
Revision = typ.NewType('Revision', str)


def increment_revision(change_id: ChangeId, rev: Revision | None) -> Revision:
    if rev is None:
        rev_num = 0
        root = change_id[:8]
    else:
        _, root, old_rev, _ = rev.rsplit("_", 3)
        rev_num = (int(old_rev, base=16) + 1) % (16 ** 6)

    now = dt.datetime.utcnow()
    return "_".join((
        now.strftime("%Y%m%d%H%M"),
        root,
        hex(rev_num)[2:].zfill(6),
        change_id[:8],
    ))


def get_doctype(doc_or_clazz: BaseDocument | DocTypeClass) -> DocType:
    if isinstance(doc_or_clazz, BaseDocument):
        doctype = doc_or_clazz.__class__
    else:
        doctype = doc_or_clazz

    return doctype.__module__ + ":" + doctype.__name__


_doc_types: dict[DocType, DocTypeClass] = {}


def load_doctype_class(datatype: str) -> DocTypeClass:
    if datatype not in _doc_types:
        module_name, class_name = datatype.split(":", 1)
        module = importlib.import_module(module_name)
        _doc_types[datatype] = getattr(module, class_name)
    return _doc_types[datatype]


class Change(pydantic.BaseModel):
    # distributed/persisted
    address: str            # affiliation
    opcode : str
    opdata : dict[str, typ.Any]
    doctype: DocType
    parent : ChangeId | None
    rev: Revision
    pow_nonce: int          # for proof of work

    change_id: ChangeId     # digest of above fields
    signature: str          # signature of change.change_id


def derive_change_id(
    opcode   : str,
    opdata   : dict[str, typ.Any],
    doctype  : DocType,
    address  : str,
    parent_id   : ChangeId | None,
) -> ChangeId:
    signing_data = {
        'opcode' : opcode,
        'opdata' : opdata,
        'doctype': doctype,
        'address': address,
        'parent_id' : parent_id,
    }
    return crypto.deterministic_json_hash(signing_data)


class VerificationError(Exception):
    pass


def _is_valid_change(change: Change) -> bool:
    expected_change_id = derive_change_id(
        change.opcode, change.opdata, change.doctype, change.address, change.parent
    )
    assert change.change_id == expected_change_id, f"Invalid change_id {change.change_id} != {expected_change_id}"
    return crypto.verify(change.address, change.signature, change.change_id)


def loads_change(change_data: bytes) -> Change:
    change_dict = json.loads(change_data.decode("utf-8"))
    change      = Change(**change_dict)

    if _is_valid_change(change):
        return change
    else:
        raise VerificationError(change_data)


def dumps_change(change: Change) -> bytes:
    return json.dumps(change.dict()).encode("utf-8")


# def verify_document(doc_ref: DocumentReference) -> bool:
#     if doc_ref.signature is None:
#         return False
#     else:
#         obj       = doc_ref.document.dict()
#         hexdigest = crypto.deterministic_json_hash(obj)
#         return crypto.verify(
#             address=doc_ref.address,
#             signature=doc_ref.signature,
#             message=hexdigest,
#         )


# def sign_envelope(doc_ref: DocumentReference, wif: str) -> DocumentReference:
#     obj       = doc_ref.document.dict()
#     hexdigest = crypto.deterministic_json_hash(obj)
#     return DocumentReference(
#         address=doc_ref.address,
#         document=doc_ref.document,
#         signature=crypto.sign(hexdigest, wif),
#     )


# def verify_identity_envelope(identity_ref) -> bool:
#     valid_sig        = verify_document(doc_ref=identity_ref)
#     is_matching_addr = identity_ref.address == identity_ref.document.address
#     return is_matching_addr and valid_sig


class DocumentReference(typ.NamedTuple):
    # in memory reference (not-persisted)
    doc : BaseDocument
    head: ChangeId
    rev : Revision


class GenericDocument(BaseDocument):
    title: str
    props: dict[str, typ.Any]


class Identity(BaseDocument):
    address: str
    props  : dict[str, typ.Any]


class ChatMessage(BaseDocument):
    topic : str
    iso_ts: str
    text  : str


class IdentityResponse(pydantic.BaseModel):
    path    : str
    identity: BaseDocument


class IdentityEnvelope(pydantic.BaseModel):
    # path    : str
    # identity: BaseDocument
    pass


# maybe maybe maybe
#
# class PolicyOffer(BaseDocument):
#     pass
#
#
# class PolicyContract(BaseDocument):
#     pass
#
#
# ROLE_PLAINTIFF = "plaintiff"
# ROLE_DEFENDANT = "defendant"
# ROLE_JUDGE     = "judge"
#
#
# class ClaimAssociation(BaseDocument):
#     identity: Identity
#     role    : str
#
#
# class PolicyClaim(BaseDocument):
#     pass
