#!/usr/bin/env python
# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import json
import time
import typing as typ

import click

from guarantor import schemas
from guarantor.client import HttpClient
from guarantor.cli_util import init_option

try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency


ENV_DEFAULTS_OPTIONS = {}


def opt(name: str, helptxt: str, default: typ.Any, **kwargs) -> click.Option:
    option, env_name, _default = init_option(name, helptxt, default)
    if env_name in ENV_DEFAULTS_OPTIONS:
        assert ENV_DEFAULTS_OPTIONS[env_name] == _default
    else:
        ENV_DEFAULTS_OPTIONS[env_name] = _default
    return option


@click.group(context_settings={'help_option_names': ["-h", "--help"]})
@click.version_option(version="2022.1001-alpha")
def cli() -> None:
    """CLI for guarantor."""


@cli.command()
@opt("host"     , "IP to serve on"          , default="0.0.0.0")
@opt("port"     , "Port to serve on"        , default=21021)
@opt("db_url"   , "Database Url"            , default="sqlite:///./guarantor.sqlite3")
@opt("no_reload", "Disable realod for serve", default=False)
def serve(host: str, port: int, db_url: str, no_reload: bool) -> None:
    """Serve API app with uvicorn"""
    # pylint: disable=import-outside-toplevel
    import uvicorn

    uvicorn.run("guarantor.app:app", host=host, port=port, reload=not no_reload)


@cli.command()
@opt("urls", "Connection Urls (comma separated)", default=["http://127.0.0.1:21021"])
def info(urls: list[str]) -> None:
    http_client = HttpClient(urls)
    print(json.dumps(http_client.info()))


@cli.command()
@opt("urls", "Connection Urls (comma separated)", default=["http://127.0.0.1:21021"])
def post_identity(urls: str) -> None:
    http_client = HttpClient(urls)
    identity    = schemas.Identity(
        pubkey=str(int(time.time() * 1000)),
        info={'name': "jdoe", 'birthday': '2000-01-01', 'sex': "yes"},
    )
    print(">>>", identity)
    identity_resp = http_client.post_identity(identity)
    print("<<<", identity_resp)
    print("???", http_client.get_identity(identity.pubkey))
