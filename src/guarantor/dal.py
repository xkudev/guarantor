import typing as typ
import pathlib as pl

from guarantor import schemas
from guarantor import changedb
from guarantor import indexing


class DataAccessLayer:
    def __init__(self):
        db_dir  = pl.Path("~") / ".config" / "guarantor"
        self.db = changedb.Client(db_dir)

    def _find_matches(self, datatype: str, search_kwargs: dict) -> typ.Iterator[indexing.MatchItem]:
        for field, search_term in search_kwargs.items():
            yield from indexing.query_index(datatype, search_term, fields=[field])

    def find(self, datatype: str, **search_kwargs) -> typ.Iterator[schemas.BaseModel]:
        for match in self._find_matches(search_kwargs):
            yield self.db.get(match.model_id)

    def find_one(self, datatype: str, **search_kwargs) -> schemas.BaseModel | None:
        latest_model = None
        for model in self._find_matches(search_kwargs):
            if latest_model is None:
                latest_model = model
            else:
                # if latest_model.generation < model.generation:
                #   latest_model = model
                pass

        return latest_model

    def get(self, head_id: schemas.ModelId) -> schemas.BaseEnvelope:
        return self.db.post(head_id)

    def post(self, model: schemas.BaseModel) -> schemas.ModelId:
        return self.db.post(model)
