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
from guarantor import schemas

logger = logging.getLogger(__name__)

WIF = typ.Any


class DatabaseReference(typ.NamedTuple):
    # ephemeral/never persisted
    head_id: schemas.ModelId
    model  : schemas.BaseModel


Path = str


OP_RESET     = "reset"
OP_DICT_DIFF = "dictdiff"
OP_SET       = "set"
OP_DEL       = "del"


class Change(typ.NamedTuple):
    # NOTE (mb 2022-07-17): persisted
    parent    : schemas.ModelId | None
    opcode    : str
    opdata    : dict[str, typ.Any]
    model_type: str
    address   : str
    signature : str  # signature of {parent + op}


class Operation(typ.NamedTuple):
    opcode: str
    opdata: typ.Any


def dumps_change(change: Change) -> bytes:
    change_json = json.dumps(
        {
            'parent'    : change.parent,
            'opcode'    : change.opcode,
            'opdata'    : change.opdata,
            'model_type': change.model_type,
            'address'   : change.address,
            'signature' : change.signature,
        }
    )
    return change_json.encode("utf-8")


def loads_change(change_data: bytes) -> Change:
    change_dict = json.loads(change_data.decode("utf-8"))
    return Change(
        parent=change_dict['parent'],
        opcode=change_dict['opcode'],
        opdata=change_dict['opdata'],
        model_type=change_dict['model_type'],
        address=change_dict['address'],
        signature=change_dict['signature'],
    )


def get_signing_hash(change: Change):
    signing_data = {
        'parent'    : change.parent,
        'opcode'    : change.opcode,
        'opdata'    : change.opdata,
        'model_type': change.model_type,
    }
    return crypto.deterministic_json_hash(signing_data)


def create_change(parent: schemas.ModelId | None, model_type: str, op: Operation, wif: str) -> Change:
    signing_data = {
        'parent'    : parent,
        'opcode'    : op.opcode,
        'opdata'    : op.opdata,
        'model_type': model_type,
    }
    signing_hash = crypto.deterministic_json_hash(signing_data)
    signature    = crypto.sign(signing_hash, wif)
    address      = crypto.get_wif_address(wif)
    return Change(
        parent=parent,
        opcode=op.opcode,
        opdata=op.opdata,
        model_type=model_type,
        address=address,
        signature=signature,
    )


class VerificationError(Exception):
    pass


def verify_change(change: Change):
    return crypto.verify(change.address, change.signature, get_signing_hash(change))


def get_change_id(change: Change) -> schemas.ModelId:
    return crypto.deterministic_json_hash(change._asdict())


def doc_patch(diff: list[Operation], old_doc: dict) -> dict:
    new_doc = copy.deepcopy(old_doc)
    for op in diff:
        if op.opcode == OP_RESET:
            new_doc = op.opdata
        elif op.opcode == OP_DICT_DIFF:
            new_doc = dictdiffer.patch(op.opdata, new_doc)
        else:
            errmsg = f"doc_patch not implemended for opcode={op.opcode}"
            raise NotImplementedError(errmsg)

    return new_doc


def model_patch(op: Operation, old_model: schemas.BaseModel) -> schemas.BaseModel:
    new_doc     = doc_patch([op], old_model.dict())
    model_clazz = old_model.__class__
    return model_clazz(**new_doc)


def doc_diff(old: dict, new: dict) -> Operation:
    diff = Operation(opcode=OP_RESET, opdata=new)

    # import json
    # try:
    #     dd_diff = list(dictdiffer.diff(old, new))
    #     dd_diff = json.loads(json.dumps(dd_diff))
    #     maybe_op = Operation(opcode=OP_DICT_DIFF, data=dd_diff)
    #     if doc_patch(maybe_op, old) == new:
    #         diff = maybe_op
    #     else:
    #         logger.warning("dictdiffer failed")
    # except ValueError:
    #     raise

    return diff


def model_diff(old: schemas.BaseModel, new: schemas.BaseModel) -> Operation:
    return doc_diff(old.dict(), new.dict())


def _build_model(changes: list[Change]) -> schemas.BaseModel:
    model_types = {change.model_type for change in changes}
    if len(model_types) != 1:
        raise ValueError(f"integrity error: ambiguous types {model_types}")

    full_diff: list[Operation] = []
    for change in changes:
        full_diff.append(Operation(change.opcode, change.opdata))

    full_doc = doc_patch(reversed(full_diff), old_doc={})

    model_type = next(iter(model_types))
    return schemas.load_model_type(model_type)(**full_doc)


class Client:
    def __init__(self, db_dir: pl.Path, flag: str = 'r'):
        self.db_dir = db_dir
        self.flag   = flag

    def dbm_path(self, change_id: schemas.ModelId):
        # NOTE (mb 2022-07-24): To keep file sizes managable, and to reduce
        #   multithreading contention, we might shard based on change_id.
        return self.db_dir / "db.dbm"

    def _get_change(self, change_id: schemas.ModelId) -> typ.Optional[Change]:
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

    def _iter_changes(self, head_id: schemas.ModelId, early_exit: bool = False) -> typ.Iterator[Change]:
        change_id = head_id
        while change := self._get_change(change_id):
            yield change
            if early_exit and change.opcode == OP_RESET:
                return
            change_id = change.parent

    def get(self, change_id: schemas.ModelId) -> schemas.BaseModel:
        changes = list(self._iter_changes(change_id, early_exit=True))
        return _build_model(changes)

    def _put_change(self, change: Change) -> schemas.ModelId:
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
        model   : schemas.BaseModel,
        wif     : str,
        prev_ref: DatabaseReference | None = None,
    ) -> schemas.ModelId:
        datatype = schemas.get_datatype(model)

        if prev_ref is None:
            new_op = Operation(OP_RESET, model.dict())
        else:
            new_op = model_diff(old=prev_ref.model, new=model)

        parent  = (prev_ref and prev_ref.head_id) or None
        change  = create_change(parent=parent, model_type=datatype, op=new_op, wif=wif)
        head_id = self._put_change(change)
        return DatabaseReference(head_id, model)
