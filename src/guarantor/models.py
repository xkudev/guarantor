# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import sqlalchemy as sa

# from guarantor import schemas
from guarantor import database

# from sqlalchemy import Column, ForeignKey, Integer, String, Float
# from sqlalchemy.types import JSON


class Identity(database.Base):
    __tablename__ = "identities"

    dbid    = sa.Column(sa.Integer, primary_key=True, index=True)
    address = sa.Column(sa.String , nullable=False  , unique=True)
    props   = sa.Column(sa.Text   , nullable=False)
