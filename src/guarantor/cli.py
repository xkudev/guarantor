#!/usr/bin/env python
# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import sys
import json
import typing as typ
import logging
import pathlib as pl

import click

from guarantor import cli_util

try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency


logger = logging.getLogger("guarantor.cli")


ENV_DEFAULTS_OPTIONS: dict[str, typ.Any] = {}


def init_client(urls: list[str]):
    # pylint: disable=import-outside-toplevel
    from guarantor.client import HttpClient

    return HttpClient(urls)


arg = click.argument


def opt(name: str, helptxt: str, default: typ.Any, **kwargs) -> typ.Any:
    option, env_name, _default = cli_util.init_option(name, helptxt, default)
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

    from guarantor import database

    database.DB_URL = db_url
    uvicorn.run("guarantor.app:app", host=host, port=port, reload=not no_reload)


@cli.command()
@opt("profile", "Profile name"                     , default="default_profile")
@opt("urls"   , "Connection Urls (comma separated)", default=["http://127.0.0.1:21021"])
def info(profile: str, urls: list[str]) -> None:
    profile_obj = cli_util.read_profile(profile)
    if profile_obj is None:
        logger.info("No profile data")
    else:
        print(json.dumps(profile_obj))

    http_client = init_client(urls)
    print(json.dumps(http_client.info()))


@cli.command()
@opt("profile", "Profile name", default="default_profile")
def update_profile(profile: str) -> None:
    try:
        profile_obj = cli_util.read_profile(profile) or {}

        # TODO (mb 2022-06-26):

        # profile_properties = ["full_name", "email", "twitter"]
        # for prop_name in profile_properties:
        #     profile_obj[prop_name] = click.prompt(f"Please enter your {prop_name}", type=str)

        cli_util.update_profile(profile, profile_obj)
    except cli_util.UserError as err:
        logger.error(f"error - {err.args[0]}")
        sys.exit(err.args[1])


@cli.command()
@opt("profile", "Profile name"                     , default="default_profile")
@opt("urls"   , "Connection Urls (comma separated)", default=["http://127.0.0.1:21021"])
def post_identity(profile: str, urls: list[str]) -> None:
    # pylint: disable=import-outside-toplevel
    from guarantor import schemas

    profile_obj = cli_util.read_profile(profile) or {}
    identity    = schemas.Identity(
<<<<<<< HEAD
        address="1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv",
        info={'name': "jdoe", 'birthday': '2000-01-01', 'sex': "yes"},
||||||| constructed merge base
        pubkey=str(int(time.time() * 1000)),
        info={'name': "jdoe", 'birthday': '2000-01-01', 'sex': "yes"},
=======
        pubkey=str(int(time.time() * 1000)),
        info=profile_obj,
>>>>>>> wip chitcaht
    )
    print(">>>", identity)

    http_client   = init_client(urls)
    identity_resp = http_client.post_identity(identity)
    print("<<<", identity_resp)
<<<<<<< HEAD
    print("???", http_client.get_identity(identity.address))
||||||| constructed merge base
    print("???", http_client.get_identity(identity.pubkey))
=======
    print("???", http_client.get_identity(identity.pubkey))


# @cli.command()
# @opt("profile", "Profile name"      , default="default_profile")
# @opt("urls"   , "Connection Urls (comma separated)", default=["http://127.0.0.1:21021"])
# def init(profile: str, urls: list[str]) -> None:
#     try:
#         profile_obj = cli_util.read_profile(profile)

#     except cli_util.UserError as err:
#         logger.error(f"error - {err.args[0]}")
#         sys.exit(err.args[1])


@cli.command()
@arg("user")
@opt("profile", "Profile name"                     , default="default_profile")
@opt("urls"   , "Connection Urls (comma separated)", default=["http://127.0.0.1:21021"])
def add_contact(user: str, profile: str, urls: list[str]) -> None:
    profile_obj = cli_util.read_profile(profile)

    contacts  = init_client(urls).find_contacts(user)
    if len(contacts) == 0:
        print(f'''{"error": "No identity found for username/uuid : '{user}'"}''')
    elif len(contacts) == 1:
        contact_identity = contacts[0]
        profile_obj['aliases'][user] = contact_identity['uuid']
        profile_obj['aliases'][contact_identity['username']] = contact_identity['uuid']
        profile_obj['aliases'][contact_identity['uuid']] = contact_identity['uuid']
        profile_obj['contacts'][contact_identity['uuid']] = contact_identity
    elif len(contacts) > 1:
        err = {
            'error'     : "Ambiguous username/uuid : '{user}'",
            'contacts': [{'uuid': ident['uuid'], 'username': ident['username']} for ident in identities],
        }
        print(json.dumps(err))


@cli.command()
@arg("user")
@arg("text")
@opt("profile", "Profile name", default="default_profile")
def msg(user: str, text: str, profile: str) -> None:
    profile_obj = cli_util.read_profile(profile)

    if user not in profile_obj['contacts']:
        identities = init_client(urls).find_contacts(user)


    # recipient:  = None
>>>>>>> wip chitcaht
