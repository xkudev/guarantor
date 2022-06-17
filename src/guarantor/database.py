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

SQLALCHEMY_DB_URL = os.getenv('GUARANTOR_SQLALCHEMY_DB_URL', "sqlite:///./guarantor.db")

connect_args = {}

if SQLALCHEMY_DB_URL.startswith("sqlite://"):
    connect_args['check_same_thread'] = False


engine       = create_engine(SQLALCHEMY_DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


session = fastapi.Depends(get_db)
