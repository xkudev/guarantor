# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import sys
import time
import typing as typ
import logging

import requests
import websocket

from guarantor import schemas

logger = logging.getLogger("guarantor.client")


Headers = dict[str, str]

ResponseData = dict[str, typ.Any]

DEFAULT_API_VERSION = "v1"


def request_to_curl(req: requests.PreparedRequest) -> str:
    headers = "".join(
        f' \\\n\t -H "{k}: {v}"' for k, v in req.headers.items() if k not in ('Content-Length',)
    )
    body = req.body
    if isinstance(body, bytes):
        content = body.decode('utf-8')
        data    = f" \\\n\t -d '{content}'"
    elif isinstance(body, str):
        data = f" \\\n\t -d '{body}'"
    else:
        data = ""
    return f"curl -X {req.method} '{req.url}' {headers} {data}"


class HttpClient:
    """Python interface, wrapping the Rest API."""

    def __init__(self, urls: list[str], api_version: str = DEFAULT_API_VERSION, verbose: int = 0) -> None:
        self.urls        = urls
        self.api_version = api_version
        self.verbose     = verbose

    def request(
        self,
        *path_parts: str,
        method : str,
        headers: Headers | None = None,
        payload: str     | None = None,
    ) -> requests.Response:
        if headers is None:
            _headers = {}
        else:
            _headers = headers

        if payload and 'Content-Type' not in _headers:
            _headers['Content-Type'] = "application/json"

        # TODO (mb 2022-06-26): failover/load balancing
        base_url = self.urls[0].rstrip("/")
        path     = f"/{self.api_version}/" + "/".join(path_parts)
        path     = path.replace("//", "/")
        url      = base_url + path
        logger.info(f"{method} {url}")

        response = requests.request(
            method,
            url=url,
            # params=params,
            data=payload,
            headers=_headers,
        )
        if self.verbose > 1:
            logger.debug(request_to_curl(req=response.request))

        if not response.ok:
            sys.stderr.write(response.content.decode("utf-8") + "\n")
            response.raise_for_status()

        return response

    def get(self, *args, **kwargs) -> requests.Response:
        kwargs['method'] = 'GET'
        return self.request(*args, **kwargs)

    def post(self, *args, **kwargs) -> requests.Response:
        kwargs['method'] = 'POST'
        return self.request(*args, **kwargs)

    def info(self) -> ResponseData:
        return self.get('info').json()  # type: ignore

    def post_identity(self, identity: schemas.Identity) -> ResponseData:
        response = self.post('identity', payload=identity.json())
        return response.json()  # type: ignore

    def get_identity(self, pubkey: str) -> ResponseData:
        response = self.get('identity', pubkey)
        return response.json()  # type: ignore

    def chat(self, msg: schemas.ChatMessage) -> ResponseData:
        response = self.post(f"/chat/{msg.topic}/", payload=msg.json())
        return response.json()  # type: ignore

    async def listen(self, topic: str) -> typ.AsyncGenerator[str, None]:
        for http_base_url in self.urls:
            http_proto, url_part = http_base_url.split("://", 1)
            assert http_proto in ("http", "https")
            ws_proto     = "ws" if http_proto == "http" else "https"
            ws_base_url  = ws_proto    + "://" + url_part
            ws_topic_url = ws_base_url + f"/v1/chat/{topic}/"

            retries = 0
            while retries < 5:
                try:
                    ws = websocket.WebSocket()
                    ws.connect(ws_topic_url)
                    while True:
                        message = ws.recv()
                        retries = 0
                        if message == 'close':
                            break
                        else:
                            yield message

                    ws.close()
                except (
                    ConnectionResetError,
                    ConnectionRefusedError,
                    websocket.WebSocketConnectionClosedException,
                ):
                    ws.close()
                    retries = retries + 1
                    sleep   = 200 * 2 ** retries
                    time.sleep(sleep / 1000)
                    print(f"retry {retries} after {sleep} ms")
