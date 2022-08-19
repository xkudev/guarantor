# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT

"""An Key Value Database for document storage.

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
- Fast random access reads
"""
import dbm
import typing as typ
import logging
import pathlib as pl

from guarantor import docdiff
from guarantor import schemas

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, db_dir: str | pl.Path, flag: typ.Literal['r', 'c'] = 'r'):
        self.db_dir = pl.Path(db_dir)
        self.flag   = flag

    def dbm_path(self, change_id: schemas.ChangeId) -> pl.Path:
        # pylint: disable=unused-argument; change_id is to allow for future sharding
        # NOTE (mb 2022-07-24): To keep file sizes managable, and to reduce
        #   multithreading contention, we might shard based on change_id.
        return self.db_dir / "db.dbm"

    def iter_changes(self, head: schemas.ChangeId, early_exit: bool = False) -> typ.Iterator[schemas.Change]:
        path = self.dbm_path(head)
        with dbm.open(str(path), flag='r') as db:

            current_id: schemas.ChangeId | None = head

            while change_data := (current_id and db.get(current_id)):
                change = schemas.loads_change(change_data)
                yield change

                if early_exit and change.opcode == docdiff.OP_RESET:
                    return

                current_id = change.parent_id

    def get(self, change_id: schemas.ChangeId) -> schemas.Change | None:
        try:
            return next(iter(self.iter_changes(change_id)))
        except StopIteration:
            return None
        except dbm.error as err:
            if "doesn't exist" in str(err):
                return None
            else:
                raise

    def post(self, change: schemas.Change) -> None:
        if not schemas.verify_change(change):
            raise ValueError("Invalid change!")

        path = self.dbm_path(change.change_id)
        if self.flag == 'r':
            raise Exception(f"dbm open for {path} not possible with flag='r'")

        change_data = schemas.dumps_change(change)
        with dbm.open(str(path), flag=self.flag) as db:
            db[change.change_id] = change_data
