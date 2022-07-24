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
import dbm
import copy
import json
import typing as typ
import logging
import pathlib as pl

import dictdiffer

from guarantor import crypto

logger = logging.getLogger(__name__)

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
    parent     : ChangeHash | None
    op         : Operation
    schema_name: str
    address    : str
    signature  : str  # signature of {parent + op}


def dumps_change(change: Change) -> bytes:
    change_json = json.dumps(
        {
            'parent'     : change.parent,
            'op'         : change.op._asdict(),
            'schema_name': change.schema_name,
            'address'    : change.address,
            'signature'  : change.signature,
        }
    )
    return change_json.encode("utf-8")


def loads_change(change_data: bytes) -> Change:
    change_dict = json.loads(change_data.decode("utf-8"))
    op_dict     = change_dict['op']
    return Change(
        parent=change_dict['parent'],
        op=Operation(opcode=op_dict['opcode'], data=op_dict['data']),
        schema_name=change_dict['schema_name'],
        address=change_dict['address'],
        signature=change_dict['signature'],
    )


def get_signing_hash(change: Change):
    signing_data = {'parent': change.parent, 'op': change.op._asdict(), 'schema_name': change.schema_name}
    return crypto.deterministic_json_hash(signing_data)


def create_change(parent: ChangeHash | None, schema_name: str, op: Operation, wif: str) -> Change:

    signing_data = {'parent': parent, 'op': op._asdict(), 'schema_name': schema_name}
    signing_hash = crypto.deterministic_json_hash(signing_data)
    signature    = crypto.sign(signing_hash, wif)
    address      = crypto.get_wif_address(wif)
    return Change(
        parent=parent,
        op=op,
        schema_name=schema_name,
        address=address,
        signature=signature,
    )


class VerificationError(Exception):
    pass


def verify_change(change: Change):
    return crypto.verify(change.address, change.signature, get_signing_hash(change))


def get_change_id(change: Change) -> ChangeHash:
    return crypto.deterministic_json_hash(change._asdict())


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

    # import json
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
    def __init__(self, dht_cache_dir: pl.Path, flag: str = 'r'):
        self.dht_cache_dir = dht_cache_dir
        self.flag          = flag

    def dbm_path(self, change_id: ChangeHash):
        # NOTE (mb 2022-07-24): To keep file sizes managable, and to reduce
        #   multithreading contention, we might shard based on change_id.
        return self.dht_cache_dir / "db.dbm"

    def _get_change(self, change_id: ChangeHash) -> typ.Optional[Change]:
        path = self.dbm_path(change_id)

        try:
            with dbm.open(str(path), flag="r") as db:
                change_data = db.get(change_id)
                change      = loads_change(change_data)
                if verify_change(change):
                    return change
                else:
                    raise VerificationError(change_id)
        except dbm.error as err:
            if "doesn't exist" in str(err):
                return None
            else:
                raise

    def _iter_changes(self, head_id: ChangeHash, early_exit: bool = False) -> typ.Iterator[Change]:
        change_id = head_id
        while change := self._get_change(change_id):
            yield change
            if early_exit and change.op.opcode == OP_RESET:
                return
            change_id = change.parent

    def get(self, change_id: ChangeHash) -> Document:
        changes = list(self._iter_changes(change_id, early_exit=True))
        return _build_document(changes)

    def _put_change(self, change: Change) -> ChangeHash:
        if not verify_change(change):
            raise ValueError("Invalid change!")

        change_id = get_change_id(change)
        path      = self.dbm_path(change_id)
        if self.flag == 'r':
            raise Exception(f"dbm open for {path} not possible with flag='r'")

        change_data = dumps_change(change)
        with dbm.open(str(path), flag=self.flag) as db:
            db[change_id] = change_data

        return change_id

    def post(
        self,
        doc        : Document,
        schema_name: str,
        wif        : str,
        prev_doc   : DatabaseDocument | None = None,
    ) -> ChangeHash:
        if prev_doc is None:
            new_doc_op = Operation(opcode=OP_RESET, data=doc)
        else:
            new_doc_op = doc_diff(old=prev_doc.raw_document, new=doc)

        parent  = (prev_doc and prev_doc.head_id) or None
        change  = create_change(parent=parent, schema_name=schema_name, op=new_doc_op, wif=wif)
        head_id = self._put_change(change)
        return DatabaseDocument(head_id, copy.deepcopy(doc))
