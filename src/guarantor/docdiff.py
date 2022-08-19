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

WIF = typ.Any


Path = str


OP_RESET     = "reset"
OP_DICT_DIFF = "dictdiff"
OP_SET       = "set"
OP_DEL       = "del"


class Operation(typ.NamedTuple):
    opcode: str
    opdata: typ.Any


def make_change(
    doctype   : str,
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
        parent_id=parent and parent.change_id,
        parent_rev=parent and parent.rev,
        difficulty=difficulty,
    )


def apply_diffs(diff: list[Operation], old_doc: dict) -> dict:
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


def doc_patch(op: Operation, old_doc: schemas.BaseDocument) -> schemas.BaseDocument:
    new_doc   = apply_diffs([op], old_doc.dict())
    doc_class = old_doc.__class__
    return doc_class(**new_doc)


def make_diff(old_doc_kw: dict, new_doc_kw: dict) -> Operation:
    diff_op = Operation(opcode=OP_RESET, opdata=new_doc_kw)

    # TODO (mb 2022-08-19): More efficient diff operations (and possibly also do chunking
    #   here so lower layers don't need to deal with huge changes).
    #
    # import json
    # try:
    #     dd_diff = list(dictdiffer.diff(old_doc_kw, new_doc_kw))
    #     dd_diff = json.loads(json.dumps(dd_diff))
    #     maybe_op = Operation(opcode=OP_DICT_DIFF, data=dd_diff)
    #     is_valid_op = apply_diffs([maybe_op], old_doc_kw) == new_doc_kw
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
    full_diff: list[Operation] = [Operation(change.opcode, change.opdata) for change in changes]
    full_diff.reverse()
    full_doc = apply_diffs(full_diff, old_doc={})

    doctype_str   = changes[-1].doctype
    doctype_class = schemas.load_doctype_class(doctype_str)
    return doctype_class(**full_doc)
