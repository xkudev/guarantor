# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import os

import fastapi
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# import fastapi_sqlalchemy

DB_URL = os.getenv('GUARANTOR_DB_URL', "sqlite:///./guarantor.sqlite3")

connect_args = {}

if DB_URL.startswith("sqlite://"):
    connect_args['check_same_thread'] = False
else:
    raise NotImplementedError(f"No db implementation for {DB_URL}")


engine       = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


session = fastapi.Depends(get_db)
