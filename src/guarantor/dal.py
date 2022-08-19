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
    def __init__(self, db_dir: str | pl.Path = env.DEFAULT_DB_DIR, wif: str | None = None):
        self.store = kvstore.Client(db_dir, flag='c')
        self.wif   = wif

    def get(self, head: schemas.ChangeId) -> 'DocumentWrapper':
        # TODO (mb 2022-08-07): async, to encourage batching?
        doc_ref = self.store.get(head)
        changes = list(self.store.iter_changes(head))
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

    def _post(self, change: 'DocumentWrapper') -> 'DocumentWrapper':
        # TODO (mb 2022-07-29): The wif should probably not be passed to the db.
        #   Instead all code related to the wif should be pulled up here and what
        #   we post to the db is the already signed change.
        ref = self.store.post(change)
        indexing.update_indexes(ref.head_id, doc)
        return ref

    def new(self, clazz: schemas.DocTypeClass, **kwargs) -> 'DocumentWrapper':
        obj = clazz(**kwargs)
        op  = docdiff.Operation(docdiff.OP_RESET, new_doc_kw)
        return DocumentWrapper(self, obj, change.id)


class DocumentWrapper:

    _dal: DataAccessLayer
    doc : schemas.BaseDocument
    head: schemas.ChangeId | None
    rev : schemas.Revision

    def __init__(
        self,
        dal : DataAccessLayer,
        doc : schemas.BaseDocument,
        head: schemas.ChangeId | None = None,
        rev : schemas.Revision = -1,
    ):
        self._dal = dal
        self.doc  = doc
        self.head = head
        self.rev  = rev

    def update(self, **updated_doc_kwargs) -> 'DocumentWrapper':
        old_doc_kw = self.doc.dict()
        new_doc_kw = old_doc_kw.copy()
        for key, val in updated_doc_kwargs.items():
            new_doc_kw[key] = val

        op     = docdiff.make_diff(old=old_doc_kw, new=new_doc_kw)
        change = docdiff.create_change(parent=self.doc.head, op=op)

        parent = (parent and parent.head) or None
        change = docdiff.create(
            parent=parent,
            doctype=schemas.get_doctype(doc),
            op=new_op,
            wif=self._dal.wif,
        )
        ref = self._dal.store.post(change)

        new_head = self._dal.post(change)
        new_rev  = schemas.increment_revision(self.rev, change.change_id)
        return DocumentWrapper(dal=self._dal, doc=new_doc, head=change.change_id, rev=new_rev)

    def __eq__(self, other: 'DocumentWrapper') -> bool:
        return self._head == other._head
