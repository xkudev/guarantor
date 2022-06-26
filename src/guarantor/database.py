# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import os
import typing as typ

import fastapi
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

# import fastapi_sqlalchemy

Base = declarative_base()

DB_URL = os.getenv('GUARANTOR_DB_URL', "sqlite:///./guarantor.sqlite3")


DB_SESSION_CLASSES: dict[str, typ.Callable[[], sa.orm.Session]] = {}


def _init_session_local(db_url: str) -> sa.orm.Session:
    if db_url in DB_SESSION_CLASSES:
        session_local_class = DB_SESSION_CLASSES[db_url]
    else:
        connect_args = {}

        if db_url.startswith("sqlite://"):
            connect_args['check_same_thread'] = False
        else:
            raise NotImplementedError(f"No db implementation for {db_url}")

        engine              = sa.create_engine(db_url, connect_args=connect_args)
        session_local_class = sa.orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)
        DB_SESSION_CLASSES[db_url] = session_local_class

    return session_local_class()


def get_db():
    db = _init_session_local(DB_URL)
    try:
        yield db
    finally:
        db.close()


session = fastapi.Depends(get_db)
