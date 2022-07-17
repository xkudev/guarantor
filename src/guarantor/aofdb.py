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
import enum
import typing as typ
import pathlib as pl
from guarantor import crypto

WIF      = typ.Any

Document = dict

Hash = str

Path = str


class OpCode(enum.Enum):
    SET = "set"
    DEL = "del"


class Operation(typ.NamedTuple):
    opcode: OpCode
    data  : typ.Any


class Change(typ.NamedTuple):
    # NOTE (mb 2022-07-17): persisted
    parent   : Hash | None
    ops      : list[Operation]
    address  : str
    signature: str  # signature of {parent + ops}


# KV-DB: hash -> {change}
_KVDB = {}  # hash -> change


def get_signing_hash(change: Change):
    return crypto.deterministic_json_hash({
        'parent': change.parent,
        'ops': change.ops,
    })


def create_change(parent: Hash | None, ops : list[Operation]) -> Change:
    signing_hash = crypto.deterministic_json_hash({
        'parent': parent,
        'ops': ops,
    })
    signature = crypto.sign(signing_hash, wif)
    address = crypto.get_wif_address(wif)
    return Change(
        parent=parent,
        ops=ops,
        address=address,
        signature=signature,
    )


def verify_change(change: Change):
    return crypto.verfy(
        chagnge.address,
        change.signature,
        get_signing_hash(change)
    )


def get_change_id(change: Change) -> Hash:
    return crypto.deterministic_json_hash(change._asdict())


def get_change(change_id: Hash):
    return _KVDB.get(doc_id)


def put_change(change: Change):
    change_id = get_change_id(change)
    if not verify_change(change):
        raise ValueError("Invalid change!")
    _KVDB[change_id] = change
    return change_id
    
    
def iter_change(head_change_id: Hash) -> iterator[Change]:
    change_id = head_change_id
    while change := get_change(change_id):
        yield change
        change_id = change.parent


def build_document(head_change_id)
    changes = list(iter_change(head_change_id))
    # FIXME interpret ops here


# v1: {"state": 1}
# v2: {"state": 2, "branch": {"subbranch": 2}}
# ops [v1->v2]:
#   set, .state


def _diff(old: Document, new: Document) -> list[Operation]:
    op = Operation(opcode=OpCode.REPLACE, new)
    return [op]


def _patch(update: Change, ) -> Document:
    pass


def _sign_update(ops: list[Operation], parent: Hash | None, wif: WIF) -> Change:
    return


def _update(doc: Hash, key: WIF) -> Change:
    # what actually happens
    pass


# TODO (mb 2022-07-17): better document
# class Document(typ.NamedTuple)


class Client:
    def __init__(self, dirpath: pl.Path, mode='r'):
        self.dirpath = dirpath

    def update(self, doc: Hash, key: WIF, old_doc: Document | None) -> Change:
        pass

    # def update(self, doc: Document, key: WIF, old_doc: Document | None) -> Change:
    #     # user friendly
    #     key = BTC.parse.wif(wif)

    #     pass

    def _append(self, op: Operation) -> None:
        pass
