# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import json
import math
import typing as typ
import hashlib
import datetime as dt
import importlib

import pydantic

from guarantor import crypto

ChangeId = str

BaseDocument = pydantic.BaseModel
DocTypeClass = typ.Type[BaseDocument]

DocType  = typ.NewType('DocType', str)
Revision = typ.NewType('Revision', str)


def increment_revision(doctype: DocType, change_id: ChangeId, rev: Revision | None) -> Revision:
    doctype_cleanded = doctype.replace(":", "_").replace(".", "_").lower()
    if rev is None:
        root_id = change_id[:8]
        rev_num = 0
    else:
        _, root_id, old_rev, _ = rev.split("_", 3)
        rev_num = (int(old_rev, base=16) + 1) % (16 ** 8)

    now     = dt.datetime.utcnow()
    ts_str  = now.strftime("%Y%m%d%H%M")
    rev_hex = hex(rev_num)[2:].zfill(8)
    return Revision(f"{ts_str}_{root_id}_{rev_hex}_{change_id[:8]}_{doctype_cleanded}")


def get_doctype(doc_or_clazz: BaseDocument | DocTypeClass) -> DocType:
    if isinstance(doc_or_clazz, BaseDocument):
        doctype = doc_or_clazz.__class__
    else:
        doctype = doc_or_clazz

    return DocType(doctype.__module__ + ":" + doctype.__name__)


_doc_types: dict[DocType, DocTypeClass] = {}


def load_doctype_class(doctype: DocType) -> DocTypeClass:
    if doctype not in _doc_types:
        module_name, class_name = doctype.split(":", 1)
        module = importlib.import_module(module_name)
        _doc_types[doctype] = getattr(module, class_name)
    return _doc_types[doctype]


class Change(pydantic.BaseModel):
    # distributed/persisted
    address  : str  # author/affiliation
    doctype  : DocType
    opcode   : str
    opdata   : dict[str, typ.Any]
    parent_id: ChangeId | None

    change_id: ChangeId  # digest of above fields
    rev      : Revision
    signature: str  # signature of change_id + rev

    # NOTE (mb 2022-08-18): The pow is not part of the signature, so
    #   that a new pow can be supplied, to help keep a change alive.
    # NOTE (mb 2022-08-18): The pow can only be to mitigate spam.
    #    Ultimately other criteria are more important when it comes to
    #    the eviction policy of a node.
    proof_of_work: str

    def __lt__(self, other: 'Change') -> bool:
        return self.rev < other.rev

    def __le__(self, other: 'Change') -> bool:
        return self.rev <= other.rev

    def __gt__(self, other: 'Change') -> bool:
        return self.rev > other.rev

    def __ge__(self, other: 'Change') -> bool:
        return self.rev >= other.rev


CHANGE_ID_FIELDS = ['address', 'doctype', 'opcode', 'opdata', 'parent_id']


def derive_change_id(change: Change) -> ChangeId:
    change_fields = change.dict()
    field_values  = [change_fields[field] for field in CHANGE_ID_FIELDS]
    return crypto.deterministic_json_hash(field_values)


DEFAULT_DIFFICULTY_BITS = 12


def calculate_pow(change_id: ChangeId, difficulty: int = DEFAULT_DIFFICULTY_BITS) -> str:
    assert difficulty < 40

    target = 2 ** (60 - difficulty)
    nonce  = 0
    while True:
        data   = (change_id + str(nonce)).encode("ascii")
        digest = hashlib.sha1(data).hexdigest()[:15]
        if int(digest, 16) < target:
            return f"POWv0${nonce}${digest}"

        nonce += 1


def get_pow_difficulty(change_id: str, pow_str: str) -> float:
    version, nonce, digest = pow_str.split("$")
    assert version == "POWv0"

    data   = (change_id + str(nonce)).encode("ascii")
    digest = hashlib.sha1(data).hexdigest()[:15]
    return 60 - math.log2(int(digest, 16))


def _is_valid_change(change: Change) -> bool:
    expected_change_id = derive_change_id(change)
    if change.change_id == expected_change_id:
        return crypto.verify(change.address, change.signature, change.change_id + change.rev)
    else:
        raise AssertionError(f"Invalid change_id {change.change_id} != {expected_change_id}")


def make_change(
    wif       : str,
    doctype   : DocType,
    opcode    : str,
    opdata    : dict[str, typ.Any],
    parent_id : ChangeId | None = None,
    parent_rev: Revision | None = None,
    difficulty: int = DEFAULT_DIFFICULTY_BITS,
) -> Change:
    address = crypto.get_wif_address(wif)
    change  = Change(
        address=address,
        doctype=doctype,
        opcode=opcode,
        opdata=opdata,
        parent_id=parent_id,
        rev="invalid",
        change_id="invalid",
        signature="invalid",
        proof_of_work="invalid",
    )
    change.change_id     = derive_change_id(change)
    change.rev           = increment_revision(doctype, change.change_id, parent_rev)
    change.signature     = crypto.sign(message=change.change_id + change.rev, wif=wif)
    change.proof_of_work = calculate_pow(change.change_id, difficulty)
    return change


class VerificationError(Exception):
    pass


def verify_change(change: Change) -> bool:
    change_id = derive_change_id(change)
    if change.change_id == change_id:
        return crypto.verify(change.address, change.signature, message=change_id + change.rev)
    else:
        errmsg = f"change_id {change.change_id} != {change_id}"
        raise VerificationError(errmsg)


def loads_change(change_data: bytes) -> Change:
    change_dict = json.loads(change_data.decode("utf-8"))
    change      = Change(**change_dict)

    if _is_valid_change(change):
        return change
    else:
        raise VerificationError(change_data)


def dumps_change(change: Change) -> bytes:
    return json.dumps(change.dict()).encode("utf-8")


# class DocumentReference(typ.NamedTuple):
#     # in memory reference (not-persisted)
#     doc : BaseDocument
#     head: ChangeId
#     rev : Revision


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


class GenericDocument(BaseDocument):
    title: str
    props: dict[str, typ.Any]


class Identity(BaseDocument):
    address: str
    props  : dict[str, typ.Any]


# class RepsonseDetail(pydantic.BaseModel):
#     code: int
#     msg: str | None


# class BaseResponse(pydantic.BaseModel):
#     detail: RepsonseDetail


# class IdentityResponse(BaseResponse):
#     path    : str
#     identity: Identity


# class IdentityRequest(pydantic.BaseModel):
#     # path    : str
#     # identity: BaseDocument
#     pass


# class ChatMessage(BaseDocument):
#     topic : str
#     iso_ts: str
#     text  : str


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
