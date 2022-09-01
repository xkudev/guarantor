# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import copy
import typing as typ
import logging

import dictdiffer

from guarantor import schemas

logger = logging.getLogger(__name__)


Path = str


OP_RESET     = "reset"
OP_DICT_DIFF = "dictdiff"
OP_SET       = "set"
OP_DEL       = "del"


class Operation(typ.NamedTuple):
    opcode: str
    opdata: typ.Any


def make_change(
    doctype   : schemas.DocType,
    op        : Operation,
    parent    : schemas.Change | None,
    wif       : str,
    difficulty: int = schemas.DEFAULT_DIFFICULTY_BITS,
) -> schemas.Change:
    return schemas.make_change(
        wif=wif,
        doctype=doctype,
        opcode=op.opcode,
        opdata=op.opdata,
        parent_id=None if parent  is None else parent.change_id,
        parent_rev=None if parent is None else parent.rev,
        difficulty=difficulty,
    )


def apply_diffs(old_doc_kw: dict, diff: list[Operation]) -> dict:
    new_doc_kw = copy.deepcopy(old_doc_kw)
    for op in diff:
        if op.opcode == OP_RESET:
            new_doc_kw = op.opdata
        elif op.opcode == OP_DICT_DIFF:
            new_doc_kw = dictdiffer.patch(op.opdata, new_doc_kw)
        else:
            errmsg = f"doc_patch not implemended for opcode={op.opcode}"
            raise NotImplementedError(errmsg)

    return new_doc_kw


def doc_patch(old_doc: schemas.BaseDocument, op: Operation) -> schemas.BaseDocument:
    new_doc_kw = apply_diffs(old_doc.dict(), [op])
    doc_class  = old_doc.__class__
    return doc_class(**new_doc_kw)


def make_diff(old_doc_kw: dict, new_doc_kw: dict) -> Operation:
    # TODO (mb 2022-08-19): More efficient diff operations (and possibly also do chunking
    #   here so lower layers don't need to deal with huge changes).
    #
    # pylint: disable=unused-argument ; <- remove when TODO is done

    diff_op = Operation(opcode=OP_RESET, opdata=new_doc_kw)

    #
    # import json
    # try:
    #     dd_diff = list(dictdiffer.diff(old_doc_kw, new_doc_kw))
    #     dd_diff = json.loads(json.dumps(dd_diff))
    #     maybe_op = Operation(opcode=OP_DICT_DIFF, data=dd_diff)
    #     is_valid_op = apply_diffs(old_doc_kw, [maybe_op]) == new_doc_kw
    #     if is_valid_op:
    #         diff_op = maybe_op
    #     else:
    #         logger.warning("dictdiffer failed")
    # except ValueError:
    #     raise

    return diff_op


def doc_diff(old: schemas.BaseDocument, new: schemas.BaseDocument) -> Operation:
    old_doc_kw = old.dict()
    new_doc_kw = new.dict()
    return make_diff(old_doc_kw, new_doc_kw)


def build_document(changes: list[schemas.Change]) -> schemas.BaseDocument:
    changes.sort()

    full_diff: list[Operation] = [Operation(change.opcode, change.opdata) for change in changes]
    full_doc = apply_diffs(old_doc_kw={}, diff=full_diff)

    doctype_str   = changes[-1].doctype
    doctype_class = schemas.load_doctype_class(doctype_str)
    return doctype_class(**full_doc)
