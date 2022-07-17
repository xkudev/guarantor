# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT

"""An database library for document storage.

Non-Goals:
- Durability
    - Durability is not provided at the db level but via
      replication of the AOF.
- Write Performance

Goals (in order of priority):
- Consistency (Correctness):
    - We use AOF: append only log/file which we replicate and replay
- Encapsulate signing of document operations
- One writer, many readers.
- Random access read performance
- Search indexes
"""
import copy
import json
import typing as typ
import logging
import pathlib as pl

import dictdiffer

from guarantor import crypto

logger = logging.getLogger("guarantor.aofdb")

WIF = typ.Any

Document = dict

ChangeHash = str


class DatabaseDocument(typ.NamedTuple):
    # ephemeral/never persisted
    head_id     : ChangeHash
    raw_document: Document


Path = str


OP_RESET     = "reset"
OP_DICT_DIFF = "dictdiff"
OP_SET       = "set"
OP_DEL       = "del"


class Operation(typ.NamedTuple):
    opcode: str
    data  : typ.Any


Diff = list[Operation]


class Change(typ.NamedTuple):
    # NOTE (mb 2022-07-17): persisted
    parent   : ChangeHash | None
    op       : Operation
    address  : str
    signature: str  # signature of {parent + op}


# KV-DB: hash -> {change}
_KVDB = {}  # hash -> change


def get_signing_hash(change: Change):
    return crypto.deterministic_json_hash(
        {
            'parent': change.parent,
            'op'    : change.op._asdict(),
        }
    )


def create_change(parent: ChangeHash | None, op: Operation, wif: str) -> Change:
    signing_hash = crypto.deterministic_json_hash(
        {
            'parent': parent,
            'op'    : op._asdict(),
        }
    )
    signature = crypto.sign(signing_hash, wif)
    address   = crypto.get_wif_address(wif)
    return Change(
        parent=parent,
        op=op,
        address=address,
        signature=signature,
    )


class VerificationError(Exception):
    pass


def verify_change(change: Change):
    return crypto.verify(change.address, change.signature, get_signing_hash(change))


def get_change_id(change: Change) -> ChangeHash:
    return crypto.deterministic_json_hash(change._asdict())


def get_change(change_id: ChangeHash) -> Change:
    change = _KVDB.get(change_id)
    if verify_change(change):
        return change
    else:
        raise VerificationError(change_id)


def put_change(change: Change) -> ChangeHash:
    change_id = get_change_id(change)
    if verify_change(change):
        _KVDB[change_id] = change
        return change_id
    else:
        raise ValueError("Invalid change!")


def iter_changes(head_id: ChangeHash, early_exit: bool = False) -> typ.Iterator[Change]:
    change_id = head_id
    while change := get_change(change_id):
        yield change
        if early_exit and change.op.opcode == OP_RESET:
            return
        change_id = change.parent


def doc_patch(diff: Diff, old_doc: Document) -> Document:
    new_doc = copy.deepcopy(old_doc)
    for op in diff:
        if op.opcode == OP_RESET:
            new_doc = op.data
        elif op.opcode == OP_DICT_DIFF:
            new_doc = dictdiffer.patch(op.data, new_doc)
        else:
            errmsg = f"doc_patch not implemended for opcode={op.opcode}"
            raise NotImplementedError(errmsg)

    return new_doc


def doc_diff(old: Document, new: Document) -> Operation:
    diff = Operation(opcode=OP_RESET, data=new)

    # try:
    #     dd_diff = list(dictdiffer.diff(old, new))
    #     dd_diff = json.loads(json.dumps(dd_diff))
    #     maybe_diff = Operation(opcode=OP_DICT_DIFF, data=dd_diff)
    #     if doc_patch(maybe_diff, old) == new:
    #         diff = maybe_diff
    #     else:
    #         logger.warning("dictdiffer failed")
    # except ValueError:
    #     raise

    return diff


def _build_document(changes: list[Change]) -> Document:
    full_diff: list[Operation] = []
    for change in changes:
        full_diff.append(change.op)
    return doc_patch(reversed(full_diff), old_doc={})


class Client:
    def __init__(self, dirpath: pl.Path, mode='r'):
        self.dirpath = dirpath

    def get(self, change_id: ChangeHash) -> Document:
        changes = list(iter_changes(change_id, early_exit=True))
        return _build_document(changes)

    def post(
        self,
        doc     : Document | DatabaseDocument,
        wif     : str,
        prev_doc: DatabaseDocument | None = None,
    ) -> ChangeHash:
        if prev_doc is None:
            new_doc_op = Operation(opcode=OP_RESET, data=doc)
        else:
            new_doc_op = doc_diff(old=prev_doc.raw_document, new=doc)

        parent  = (prev_doc and prev_doc.head_id) or None
        change  = create_change(parent=parent, op=new_doc_op, wif=wif)
        head_id = put_change(change)
        return DatabaseDocument(head_id, copy.deepcopy(doc))

    # def find(self, query: Query) -> typ.Iterator[]:

    # def update(self, doc: Document, wif: WIF, old_doc: Document | None) -> Change:
    #     # user friendly
    #     key = BTC.parse.wif(wif)
