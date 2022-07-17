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

WIF      = typ.Any

Document = dict

Hash = str

Path = str


class OpCode(enum.Enum):
    REPLACE = "replace"
    SET = "set"
    DEL = "del"
    # PATCH = "patch" ?


class Operation(typ.NamedTuple):
    opcode: OpCode
    data  : typ.Any


class Update(typ.NamedTuple):
    # NOTE (mb 2022-07-17): persisted
    parent   : Hash | None
    ops      : list[Operation]
    address  : str
    signature: str


# v1: {"state": 1}
# v2: {"state": 2, "branch": {"subbranch": 2}}
# ops [v1->v2]:
#   set, .state


def _diff(old: Document, new: Document) -> list[Operation]:
    op = Operation(opcode=OpCode.REPLACE, new)
    return [op]


def _patch(update: Update, ) -> Document:
    pass


def _sign_update(ops: list[Operation], parent: Hash | None, wif: WIF) -> Update:
    return


def _update(doc: Hash, key: WIF) -> Update:
    # what actually happens
    pass


# TODO (mb 2022-07-17): better document
# class Document(typ.NamedTuple)


class Client:
    def __init__(self, dirpath: pl.Path, mode='r'):
        self.dirpath = dirpath

    def update(self, doc: Hash, key: WIF, old_doc: Document | None) -> Update:
        pass

    # def update(self, doc: Document, key: WIF, old_doc: Document | None) -> Update:
    #     # user friendly
    #     key = BTC.parse.wif(wif)

    #     pass

    def _append(self, op: Operation) -> None:
        pass
