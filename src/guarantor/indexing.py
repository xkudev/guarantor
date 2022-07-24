# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import bisect
import typing as typ
import collections

import pydantic
import sortedcontainers

from guarantor import crypto


class IndexDeclaration(typ.NamedTuple):
    datatype: str
    fields  : list[str]


INDEXE_DECLARATIONS = [
    IndexDeclaration(
        datatype="guarantor.schemas.Identity",
        fields=["address", "props.name", "props.email", "props.twitter"],
    ),
]


Hash = str


def _iter_terms(field_val: str) -> typ.Iterator[str]:
    # TODO (mb 2022-07-17): maybe word stemming and such
    yield field_val

    if "@" in field_val:
        yield field_val.split("@", 1)[-1]


def _get_field_val(model, field: str) -> str:
    if "." in field:
        attrname, rest_key = field.split(".", 1)
        attrval = getattr(model, attrname)
        while attrval and "." in rest_key:
            parent_key, rest_key = rest_key.split(".", 1)
            attrval = attrval and attrval.get(parent_key)

        return attrval and attrval.get(rest_key)
    else:
        attrname = field
        return getattr(model, attrname)


class IndexItem(typ.NamedTuple):
    stem: str
    model_hash: Hash


class Index:
    def __init__(self):
        self._items         = sortedcontainers.SortedList()
        self._pending_items = []

    def add(self, field_val: str, model_hash: str) -> None:
        for term in _iter_terms(field_val):
            if term is None:
                continue

            item = IndexItem(term, model_hash)
            self._pending_items.append(item)

    def find(self, term: str) -> typ.Iterator[IndexItem]:
        if self._pending_items:
            self._items.update(self._pending_items)
            self._pending_items.clear()

        idx = bisect.bisect_left(self._items, term)
        while idx < len(self._items):
            item = self._items[idx]
            if term in item.term:
                yield item
                idx = idx + 1
            else:
                break


_INDEXES = collections.defaultdict(Index)


def query_index(
    datatype: str,
    term    : str,
    fields  : list[str] | None = None,
) -> list[IndexItem]:
    for index_decl in INDEXE_DECLARATIONS:
        for field in index_decl.fields:
            index = _INDEXES[index_decl.datatype, field]
            for idx_item in index.find(term):
                print(idx_item.model_hash, idx_item.match_term)


def update_indexes(model: pydantic.BaseModel) -> list[Hash]:
    model_hash: Hash = crypto.deterministic_json_hash(model.dict())
    datatype = model.__module__ + "." + model.__class__.__name__
    for index_decl in INDEXE_DECLARATIONS:
        if index_decl.datatype == datatype:
            for field in index_decl.fields:
                if field_val := _get_field_val(model, field):
                    index     = _INDEXES[datatype, field]
                    index.add(field_val, model_hash)
