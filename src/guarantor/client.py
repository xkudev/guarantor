# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT

import typing as typ

import requests

Headers = dict[str, str]


class HttpClient:
    """Python interface, wrapping the Rest API."""

    def __init__(self, host: str, api_version: str = "v1", verbose: int = 0) -> None:
        self.host = host
        self.api_version = api_version
        self.verbose = verbose

    def request(
        self, endpoint: str, method: str = 'GET', headers: Headers | None = None
    ) -> requests.Response:
        if headers is None:
            _headers = {}
        else:
            _headers = headers

        url = f"{self.host}/{self.api_version}/{endpoint}"
        print("???", url)

        response = requests.request(
            method,
            url=url,
            # params=params,
            # data=data_text,
            headers=_headers,
        )
        return response

    def info(self) -> dict[str, typ.Any]:
        response = self.request('info')
        return response.json()  # type: ignore
