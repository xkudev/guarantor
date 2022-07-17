# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT

"""An database library for document storage.

Non-Goals:
- Durability
    - Durability is not provided at the db level but via
      replication of the AOL.
- Write Performance

Goals (in order of priority):
- Consistency (Correctness):
    - We use AOL: append only log/file which we replicate and replay
- Encapsulate signing of document operations
- One writer, many readers.
- Random access read performance
- Search indexes
"""
import enum
import typing as typ
import pathlib as pl


class OpCode(enum.Enum):
    SET = "set"
    DEL = "del"
    # PATCH = "patch"


class Operation(typ.NamedTuple):
    opcode  : OpCode
    doc_path: str
    data    : typ.Any


class Update(typ.NamedTuple):
    ops: list[Operation]


# TODO (mb 2022-07-17): better document
# class Document(typ.NamedTuple)
Document = dict
WIF      = typ.Any


class Client:
    def __init__(self, dirpath: pl.Path, mode='r'):
        self.dirpath = dirpath

    def update(self, doc: Document, key: WIF, old_doc: Document | None) -> Operation:
        pass

    def _append(self, op: Operation) -> None:
        pass
