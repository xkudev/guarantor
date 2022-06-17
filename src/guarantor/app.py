# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import json
import time
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


app.mount("/static", StaticFiles(directory="static"), name="static")


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
    identity = schemas.Identity(pubkey=db_identity.pubkey, info=json.loads(db_identity.info))
    return schemas.IdentityResponse(
        path=f"/v1/identity/{db_identity.pubkey}",
        identity=identity,
    )


@app.post("/v1/identity", response_model=schemas.IdentityResponse)
async def post_identity(identity: schemas.Identity, db: Session = database.session):
    db_identity = models.Identity(
        pubkey=identity.pubkey,
        info=json.dumps(identity.info),
    )
    db.add(db_identity)
    db.commit()
    db.refresh(db_identity)

    return _identity_response(db_identity)


@app.get("/v1/identity/{pubkey}", response_model=schemas.IdentityResponse)
async def get_identity(pubkey: str, db: Session = database.session):
    db_identity = db.query(models.Identity).filter(models.Identity.pubkey == pubkey).first()
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
