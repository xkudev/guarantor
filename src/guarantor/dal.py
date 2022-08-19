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
        return DocumentWrapper(dal=self, doc=doc, changes=[change])

    def get(self, head: schemas.ChangeId) -> 'DocumentWrapper':
        # TODO (mb 2022-08-07): async, to encourage batching?
        doc_ref = self.kvstore.get(head)
        changes = list(self.kvstore.iter_changes(head))
        doc     = docdiff.build_document(changes)
        assert doc_ref.head == head, f"Mismatched head {doc_ref.head} != {head}"
        return DocumentWrapper(dal=self, doc=doc_ref.doc, head=doc_ref.head, rev=doc_ref.rev)

    def _find_matches(self, datatype: str, search_kwargs: dict) -> typ.Iterator[indexing.MatchItem]:
        if not search_kwargs:
            raise TypeError("Missing keyword arguments: **search_kwargs")

        for field, search_term in search_kwargs.items():
            yield from indexing.query_index(datatype, search_term, fields=[field])

    def find(self, datatype: str, **search_kwargs) -> typ.Iterator['DocumentWrapper']:
        for match in self._find_matches(datatype, search_kwargs):
            yield self.get(match.doc_id)

    def find_one(self, datatype: str, **search_kwargs) -> schemas.BaseDocument | None:
        doc_wrp: DocumentWrapper | None = None
        for match in self._find_matches(datatype, search_kwargs):
            doc_wrp = self.get(match.doc_id)
            if doc_wrp is None or doc.generation < envelope.generation:
                doc = envelope

        return DocumentWrapper(dal=self, doc=doc, head=head, rev=rev)


class DocumentWrapper:

    _dal   : DataAccessLayer
    doc    : schemas.BaseDocument
    changes: list[schemas.Change]

    def __init__(
        self,
        dal    : DataAccessLayer,
        doc    : schemas.BaseDocument,
        changes: list[schemas.Change],
    ):
        self._dal    = dal
        self.doc     = doc
        self.changes = changes

    def update(self, **updated_doc_kwargs) -> 'DocumentWrapper':
        doctype = schemas.get_doctype(self.doc)

        old_doc_kw = self.doc.dict()
        new_doc_kw = old_doc_kw.copy()
        for key, val in updated_doc_kwargs.items():
            new_doc_kw[key] = val

        op     = docdiff.make_diff(old_doc_kw, new_doc_kw)
        parent = self.changes[-1]
        change = docdiff.make_change(
            doctype=doctype,
            op=op,
            parent=parent,
            wif=self._dal.wif,
            difficulty=self._dal.difficulty,
        )

        # TODO (mb 2022-08-19): also post to DHT
        self._dal.kvstore.post(change)

        new_changes = self.changes + [change]
        new_doc     = docdiff.doc_patch(op=op, doc=self.doc)

        assert docdiff.build_document(new_changes) == new_doc
        return DocumentWrapper(dal=self._dal, doc=new_doc, changes=new_changes)

    def __eq__(self, other: 'DocumentWrapper') -> bool:
        return self.head == other.head
