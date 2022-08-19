# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import typing as typ
import pathlib as pl

from guarantor import env
from guarantor import docdiff
from guarantor import kvstore
from guarantor import schemas
from guarantor import indexing


class DataAccessLayer:
    """Middleman between user code and DHT/KVStore.

    In order that user code doesn't need to care about where or how
    data is stored/retreived or signed/verified, the DataAccessLayer
    provides a generic API to interact with objects that are stored
    somewhere (which the user doesn't care about).
    """

    def __init__(
        self,
        wif       : str | None,
        db_dir    : str | pl.Path = env.DEFAULT_DB_DIR,
        difficulty: int = schemas.DEFAULT_DIFFICULTY_BITS,
    ):
        self.wif        = wif
        self.kvstore    = kvstore.Client(db_dir, flag='c')
        self.difficulty = difficulty

    def new(self, clazz: schemas.DocTypeClass, **kwargs) -> 'DocumentWrapper':
        if self.wif is None:
            raise Exception("A 'wif' needed to create a new document.")

        doc     = clazz(**kwargs)
        doc_kw  = doc.dict()
        op      = docdiff.Operation(docdiff.OP_RESET, doc_kw)
        doctype = schemas.get_doctype(clazz)
        change  = docdiff.make_change(
            doctype=doctype,
            op=op,
            parent=None,
            wif=self.wif,
            difficulty=self.difficulty,
        )
        return DocumentWrapper(dal=self, doc=doc, changes=[], tmp_changes=[change])

    def get(self, head: schemas.ChangeId) -> 'DocumentWrapper':
        # TODO (mb 2022-08-07): async, to encourage batching?
        changes = list(self.kvstore.iter_changes(head))
        changes.sort()
        assert changes[-1].change_id == head, f"Mismatched head {changes[-1].change_id} != {head}"

        doc = docdiff.build_document(changes)
        return DocumentWrapper(dal=self, doc=doc, changes=changes, tmp_changes=[])

    def _find_matches(self, doctype: str, search_kwargs: dict) -> typ.Iterator[indexing.MatchItem]:
        if not search_kwargs:
            raise TypeError("Missing keyword arguments: **search_kwargs")

        for field, search_term in search_kwargs.items():
            yield from indexing.query_index(doctype, search_term, fields=[field])

    def find(self, doctype: str, **search_kwargs) -> typ.Iterator['DocumentWrapper']:
        for match in self._find_matches(doctype, search_kwargs):
            yield self.get(match.change_id)

    def find_one(self, doctype: str, **search_kwargs) -> schemas.BaseDocument | None:
        result: DocumentWrapper | None = None
        for match in self._find_matches(doctype, search_kwargs):
            maybe_result = self.get(match.head)
            if result is None or maybe_result.head_rev > result.head_rev:
                result = maybe_result

        return result


def _verify_doc_changes(doc: schemas.BaseDocument, changes: list[schemas.Change]):
    doc_from_scratch = docdiff.build_document(changes)
    assert doc == doc_from_scratch, doc == doc_from_scratch


class DocumentWrapper:

    _dal       : DataAccessLayer
    doc        : schemas.BaseDocument
    head       : schemas.ChangeId
    head_rev   : schemas.Revision
    changes    : list[schemas.Change]
    tmp_changes: list[schemas.Change]

    def __init__(
        self,
        dal        : DataAccessLayer,
        doc        : schemas.BaseDocument,
        changes    : list[schemas.Change],
        tmp_changes: list[schemas.Change],
    ) -> None:
        self._dal = dal
        self.doc  = doc

        all_changes = sorted(changes + tmp_changes)

        self.head     = all_changes[-1].change_id
        self.head_rev = all_changes[-1].rev

        self.changes     = changes
        self.tmp_changes = tmp_changes

        _verify_doc_changes(self.doc, all_changes)

    def update(self, **updated_doc_kwargs) -> 'DocumentWrapper':
        doctype = schemas.get_doctype(self.doc)

        old_doc_kw = self.doc.dict()
        new_doc_kw = old_doc_kw.copy()
        for key, val in updated_doc_kwargs.items():
            new_doc_kw[key] = val

        op     = docdiff.make_diff(old_doc_kw, new_doc_kw)
        parent = (self.changes + self.tmp_changes)[-1]
        change = docdiff.make_change(
            doctype=doctype,
            op=op,
            parent=parent,
            wif=self._dal.wif,
            difficulty=self._dal.difficulty,
        )

        new_doc = docdiff.doc_patch(self.doc, op=op)
        return DocumentWrapper(
            dal=self._dal,
            doc=new_doc,
            changes=self.changes,
            tmp_changes=self.tmp_changes + [change],
        )

    def save(self) -> 'DocumentWrapper':
        # TODO (mb 2022-08-19): also post to DHT
        for change in self.tmp_changes:
            self._dal.kvstore.post(change)

        indexing.update_indexes(self.head, self.doc)

        return DocumentWrapper(
            dal=self._dal,
            doc=self.doc,
            changes=self.changes + self.tmp_changes,
            tmp_changes=[],
        )

    def __eq__(self, other: 'DocumentWrapper') -> bool:
        return isinstance(other, DocumentWrapper) and self.head == other.head

    # TODO (mb 2022-08-19): getattr and setattr
