#!/usr/bin/env python
# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import os
import time
import typing as typ

import click

from guarantor import schemas
from guarantor.client import HttpClient

try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency


OptionType = typ.Any


def _option_value_parser(
    default    : OptionType,
    raw_env_val: str | None,
) -> tuple[callable, bool, type, typ.Any]:
    # type is derived via default  (prototype approach)
    _type      = type(default)
    is_flag    = _type == bool
    is_squence = isinstance(default, (tuple, list, set))

    if is_squence:
        _click_type = str
    else:
        _click_type = _type

    if raw_env_val is None:
        if is_squence:
            _default = ",".join(default)
        else:
            _default = default
    elif is_flag:
        _default = raw_env_val.strip().lower() in ("1", "t", "true", "y", "yes")
    elif is_squence:
        _default = _type(val.strip() for val in raw_env_val.split(","))
    else:
        _default = _type(raw_env_val)

    def _parse_option_value(ctx, opt, opt_value: str) -> OptionType:
        if opt_value == default:
            return opt_value

        if _type in (tuple, list, set):
            opt_value = _type(val.strip() for val in opt_value.split(","))
        else:
            opt_value = _type(opt_value)

        return opt_value

    return (_parse_option_value, is_flag, _click_type, _default)


ENV_DEFAULTS_OPTIONS = {}


def _option(name: str, helptxt: str, default: OptionType, **kwargs) -> click.Option:
    assert name == name.lower()

    env_name = "GUARANTOR_" + name.upper()
    raw_env_val: str | None = os.getenv(env_name)

    callback, is_flag, _type, _default = _option_value_parser(default, raw_env_val)

    ENV_DEFAULTS_OPTIONS[env_name] = _default

    return click.option(
        "--" + name.replace("_", "-"),
        required=False,
        type=_type,
        is_flag=is_flag,
        default=_default,
        callback=callback,
        help=helptxt.ljust(20) + f"[{env_name}={_default}]",
    )


opt_urls   = _option("urls"  , "Connection Urls (comma separated)", default=["http://127.0.0.1:5050"])
opt_db_url = _option("db_url", "Database Url"                     , default="sqlite:///./guarantor.sqlite3")
opt_host   = _option("host"  , "IP to serve on"                   , default="0.0.0.0")
opt_port   = _option("port"  , "Port to serve on"                 , default=5050)


@click.group(context_settings={'help_option_names': ["-h", "--help"]})
@click.version_option(version="2022.1001-alpha")
def cli() -> None:
    """CLI for guarantor."""


@cli.command()
@opt_host
@opt_port
@opt_db_url
def serve(host: str, port: int, db_url: str) -> None:
    """Serve API app with uvicorn"""
    import uvicorn

    uvicorn.run("guarantor.app:app", host=host, port=port, reload=True)


@cli.command()
@opt_urls
def info(urls: list[str]) -> None:
    http_client = HttpClient(urls)
    print(http_client.info())


@cli.command()
@opt_urls
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
