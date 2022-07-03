# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import json
import time
import pathlib as pl
import datetime as dt

import fastapi
import fastapi.responses as resp
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

import guarantor
from guarantor import models
from guarantor import schemas
from guarantor import database
from guarantor import http_utils

# import enum
# import pydantic

app = fastapi.FastAPI()


static_dir = pl.Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=resp.RedirectResponse)
async def root():
    return "/v1/info/"


@app.get("/v1/info", response_class=http_utils.JSONResponse)
async def info():
    return {
        'name'   : "guarantor",
        'version': guarantor.__version__,
        'time'   : time.time(),
        'iso8601': dt.datetime.utcnow().isoformat(),
    }


def _identity_response(db_identity: models.Identity) -> schemas.IdentityResponse:
    identity = schemas.Identity(address=db_identity.address, info=json.loads(db_identity.info))
    return schemas.IdentityResponse(
        path=f"/v1/identity/{db_identity.address}",
        identity=identity,
    )


@app.post("/v1/identity", response_model=schemas.IdentityResponse)
async def post_identity(identity: schemas.IdentityEnvelope, db: Session = database.session):

    db_identity = models.Identity(
        address=identity.document.address,
        props=json.dumps(identity.document.props),
    )
    db.add(db_identity)
    db.commit()
    db.refresh(db_identity)

    return schemas.IdentityResponse(
        path=f"/v1/identity/{identity.document.address}",
        identity=identity,
    )


@app.get("/v1/identity/{address}", response_model=schemas.IdentityResponse)
async def get_identity(address: str, db: Session = database.session):
    db_identity = db.query(models.Identity).filter(models.Identity.address == address).first()
    return _identity_response(db_identity)


# @app.get("/testint/{param}")
# async def testint(param: int, q: int | None = None):
#     return {'message': param, 'q': q}


# class ModelName(str, enum.Enum):
#     ALEXNET = "alexnet"
#     RESNET  = "resnet"
#     LENET   = "lenet"


# @app.get("/testenum/{param}")
# async def testenum(param: ModelName):
#     return {'message': param}


# class Item(pydantic.BaseModel):
#     name : str
#     email: pydantic.EmailStr


# @app.post("/item/", response_model=Item)
# async def add_item(item: Item):
#     """Test docstring."""
#     return item
