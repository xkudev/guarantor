#!/usr/bin/env python
# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import os
import time

import click

import guarantor
from guarantor import schemas
from guarantor.client import HttpClient

try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency


def _env(name: str, default: str | None) -> (str | None):
    full_name = f"GUARANTOR_{name}"
    return os.getenv(full_name, default)


ENV_HOST = _env('HOST', default="http://127.0.0.1:8000")


host_option = click.option(
    "-h",
    "--host",
    type=str,
    required=False,
    default=(lambda: ENV_HOST),
    help="Hostname       [env: GUARANTOR_HOST]",
)


@click.group(context_settings={'help_option_names': ["-h", "--help"]})
def cli() -> None:
    """CLI for guarantor."""


@cli.command()
@click.version_option(version="2022.1001-alpha")
def version() -> None:
    """Show version number."""
    print(f"guarantor version: {guarantor.__version__}")


@cli.command()
@host_option
def info(host: str) -> None:
    http_client = HttpClient(host)
    print(http_client.info())


@cli.command()
@host_option
def post_identity(host: str) -> None:
    http_client = HttpClient(host)
    identity    = schemas.Identity(
        pubkey=str(int(time.time() * 1000)),
        info={'name': "jdoe", 'birthday': '2000-01-01', 'sex': "yes"},
    )
    print(">>>", identity)
    identity_resp = http_client.post_identity(identity)
    print("<<<", identity_resp)
    print("???", http_client.get_identity(identity.pubkey))
