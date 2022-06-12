# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import time
import datetime as dt

import fastapi
import fastapi.responses as resp
from fastapi.staticfiles import StaticFiles

import guarantor
from guarantor import http_utils

# from guarantor import models

# import enum
# import pydantic


app = fastapi.FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=resp.RedirectResponse)
async def root():
    return "/v1/info"


@app.get("/v1/info", response_class=http_utils.JSONResponse)
async def info():
    return {
        'name'   : "guarantor",
        'version': guarantor.__version__,
        'time'   : time.time(),
        'iso8601': dt.datetime.utcnow().isoformat(),
    }


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
