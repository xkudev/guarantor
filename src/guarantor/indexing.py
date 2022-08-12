# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import bisect
import typing as typ
import collections

import sortedcontainers

from guarantor import schemas


class IndexDeclaration(typ.NamedTuple):
    datatype: str
    fields  : list[str]


INDEX_DECLARATIONS = [
    IndexDeclaration(
        datatype="guarantor.schemas:GenericDocument",
        fields=['title'],
    ),
    IndexDeclaration(
        datatype="guarantor.schemas:Identity",
        fields=["address", "props.name", "props.email", "props.twitter"],
    ),
]


Hash = str


def _iter_terms(field_val: str) -> typ.Iterator[str]:
    # TODO (mb 2022-07-17): maybe word stemming, lower case and such
    yield field_val

    if field_val.lower() != field_val:
        yield field_val.lower()

    if "@" in field_val:
        yield field_val.split("@", 1)[-1]

    for word in field_val.split()[1:]:
        yield word
        if word != word.lower():
            yield word


def _get_field_val(doc, field: str) -> (str | None):
    if "." in field:
        attrname, rest_key = field.split(".", 1)
        attrval = getattr(doc, attrname)
        while attrval and "." in rest_key:
            parent_key, rest_key = rest_key.split(".", 1)
            attrval = attrval and attrval.get(parent_key)

        field_val = attrval and attrval.get(rest_key)
    else:
        attrname  = field
        field_val = getattr(doc, attrname, None)

    if field_val is None:
        return None
    else:
        return str(field_val)


class IndexItem(typ.NamedTuple):
    stem  : str
    doc_id: Hash


class MatchItem(typ.NamedTuple):
    stem    : str
    doc_id  : Hash
    datatype: str
    field   : str


class Index:
    def __init__(self):
        self._items         = sortedcontainers.SortedList()
        self._pending_items = []

    def add(self, field_val: str, doc_id: str) -> None:
        for term in set(_iter_terms(field_val)):
            # if term is None:
            #     continue
            print("???", (field_val, term))

            item = IndexItem(term, doc_id)
            self._pending_items.append(item)

    def find(self, search_term: str) -> typ.Iterator[IndexItem]:
        if self._pending_items:
            self._items.update(self._pending_items)
            self._pending_items.clear()

        idx = bisect.bisect_left(self._items, IndexItem(search_term, ""))
        while idx < len(self._items):
            item = self._items[idx]
            if item.stem.startswith(search_term):
                yield item
                idx = idx + 1
            else:
                break


IndexKey = tuple[str, str]

_INDEXES: dict[IndexKey, Index] = collections.defaultdict(Index)


def query_index(
    datatype   : str,
    search_term: str,
    fields     : list[str] | None = None,
) -> typ.Iterator[MatchItem]:
    for index_decl in INDEX_DECLARATIONS:
        if index_decl.datatype == datatype:
            _fields = set(index_decl.fields)
            if fields is not None:
                _fields = set(fields) & _fields

            for field in _fields:
                index = _INDEXES[index_decl.datatype, field]
                for idx_item in index.find(search_term):
                    yield MatchItem(
                        stem=idx_item.stem,
                        doc_id=idx_item.doc_id,
                        datatype=index_decl.datatype,
                        field=field,
                    )


def update_indexes(doc_id: str, doc: schemas.BaseDocument) -> None:
    datatype = schemas.get_doctype(doc)
    for index_decl in INDEX_DECLARATIONS:
        if index_decl.datatype == datatype:
            for field in index_decl.fields:
                if field_val := _get_field_val(doc, field):
                    index = _INDEXES[datatype, field]
                    index.add(field_val, doc_id)
