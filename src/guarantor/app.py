# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import json
import time
import asyncio
import logging
import pathlib as pl
import datetime as dt
import collections

import fastapi
import fastapi.responses as resp
import websockets.exceptions
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


logger = logging.getLogger("guarantor.app")

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
async def post_identity(identity: schemas.Identity, db: Session = database.session):
    db_identity = models.Identity(
        address=identity.address,
        info=json.dumps(identity.info),
    )
    db.add(db_identity)
    db.commit()
    db.refresh(db_identity)

    return _identity_response(db_identity)


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


# @app.post("/v1/message/{address}", response_model=schemas.AckResponse)
# async def message(pubkey: str, db: Session = database.session):
#     pass


HTML = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var topic = Date.now()
            document.querySelector("#ws-id").textContent = topic;
            var ws = new WebSocket(`ws://localhost:8000/v1/chat/${topic}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message  = document.createElement('li')
                var content  = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/v1/chat/")
async def get_chat_html():
    return resp.HTMLResponse(HTML)


Topic = str

_chatlogs: dict[Topic, list[schemas.ChatMessage]] = collections.defaultdict(list)


@app.post("/v1/chat/{topic}/", response_class=http_utils.JSONResponse)
async def post_chat_message(topic: Topic, message: schemas.ChatMessage):
    assert message.topic == topic
    _chatlogs[topic].append(message)
    message_id = len(_chatlogs[topic])
    return {'path': f"/v1/chat/{topic}/{message_id}"}


MAX_IDLE = 9


@app.websocket("/v1/chat/{topic}/")
async def chat(topic: Topic, ws: fastapi.WebSocket):
    await ws.accept()
    try:
        cursor       = 0
        last_message = time.time()

        while True:
            message = None
            if cursor < len(_chatlogs[topic]):
                msg     = _chatlogs[topic][cursor]
                message = msg.iso_ts + " - " + msg.text
                cursor += 1
            else:
                idle = time.time() - last_message
                if idle > MAX_IDLE:
                    iso_ts  = dt.datetime.utcnow().isoformat()
                    message = iso_ts + " - heartbeat"

            if message:
                try:
                    await ws.send_text(message)
                    last_message = time.time()
                except websockets.exceptions.ConnectionClosedError:
                    logger.info("client disconnect")
                    return
            else:
                await asyncio.sleep(0.1)
    except fastapi.WebSocketDisconnect:
        pass
