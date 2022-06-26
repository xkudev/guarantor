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


html = """
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
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
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


class ConnectionManager:

    def __init__(self):
        self.active_connections: list[fastapi.WebSocket] = []

    async def connect(self, ws: fastapi.WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: fastapi.WebSocket):
        self.active_connections.remove(ws)

    async def send(self, message: str, ws: fastapi.WebSocket):
        await ws.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


_manager = ConnectionManager()


@app.get("/v1/chat/")
async def get():
    return resp.HTMLResponse(html)


@app.websocket("/v1/chat/{topic}")
async def chat(ws: fastapi.WebSocket, topic: str):
    await _manager.connect(ws)
    try:
        await _manager.broadcast(f"Client #{topic} has entered the chat")
        while True:
            data = await ws.receive_text()
            await _manager.send(f"You wrote: {data}", ws)
            await _manager.broadcast(f"Client #{topic} says: {data}")
    except fastapi.WebSocketDisconnect:
        _manager.disconnect(ws)
        await _manager.broadcast(f"Client #{topic} left the chat")
