# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import os
import json
import uuid
import random
import typing as typ
import pathlib as pl
import datetime as dt

import click

from guarantor import wordlists

OptionType = typ.Any

Option = typ.Any


ENV_HOME        = os.getenv("HOME")
XDG_CONFIG_HOME = os.getenv("XDG_CONFIG_HOME", os.path.join(ENV_HOME, ".config"))
XDG_DATA_HOME   = os.getenv("XDG_DATA_HOME"  , os.path.join(ENV_HOME, ".local", "share"))

DEFAULT_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "guarantor")
DEFAULT_DATA_DIR   = os.path.join(XDG_DATA_HOME  , "guarantor")


class UserError(Exception):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message, exit_code)


def init_option(name: str, helptxt: str, default: OptionType) -> tuple[Option, str, OptionType]:
    # type is derived via default  (prototype approach)

    assert name == name.lower()

    env_name = "GUARANTOR_" + name.upper()

    _type      : typ.Callable = type(default)
    is_flag    : bool         = _type == bool
    is_sequence: bool         = isinstance(default, (tuple, list, set))
    _click_type: typ.Any      = str if is_sequence else _type

    if is_flag:
        _default = str(int(str(default).strip().lower() in ("1", "t", "true", "y", "yes")))
    elif is_sequence:
        _default = ",".join(map(str, default))
    else:
        _default = str(default)

    def _parse_option_value(ctx, opt, opt_value: str | None) -> OptionType:
        # pylint: disable=unused-argument
        raw_env_val: str | None = os.getenv(env_name)
        if opt_value is None:
            if raw_env_val is None:
                return default
            elif is_flag:
                return raw_env_val.strip().lower() in ("1", "t", "true", "y", "yes")
            elif is_sequence:
                return _type(val.strip() for val in raw_env_val.split(","))
            else:
                return _type(raw_env_val)
        else:
            if opt_value == default:
                return opt_value
            if is_sequence:
                return _type(val.strip() for val in opt_value.split(","))
            else:
                return _type(opt_value)

    option = click.option(
        "--" + name.replace("_", "-"),
        required=False,
        type=_click_type,
        is_flag=is_flag,
        callback=_parse_option_value,
        help=helptxt.ljust(20) + f"[evn:{env_name}]",
    )
    return (option, env_name, _default)


def new_username() -> str:
    nonce = str(random.randint(2, 9) * 10 + random.randint(1, 9))
    return random.choice(wordlists.ADJECTIVES) + "-" + random.choice(wordlists.NAMES) + "-" + nonce


Profile = typ.NewType('Profile', typ.Any)


def update_profile(profile: str, profile_obj: Profile) -> None:
    data_dir         = pl.Path(DEFAULT_DATA_DIR)
    profile_path     = data_dir / (profile + ".json")
    tmp_profile_path = data_dir / (profile + ".json.tmp")

    data_dir.mkdir(parents=True, exist_ok=True)

    profile_data = json.dumps(profile_obj)
    with tmp_profile_path.open(mode="w", encoding="utf-8") as fobj:
        fobj.write(profile_data)

    tmp_profile_path.rename(profile_path)
    return profile_obj


def read_profile(profile: str) -> Profile:
    profile_path = pl.Path(DEFAULT_DATA_DIR) / (profile + ".json")

    if profile_path.exists():
        with profile_path.open(mode="r", encoding="utf-8") as fobj:
            profile_dict = json.load(fobj)
        return Profile(profile_dict)
    else:
        anon_profile = Profile(
            {
                'uuid'    : str(uuid.uuid4()),
                'username': new_username(),
                'location': "cyberspace",
                'creation': dt.datetime.utcnow().isoformat(),
                'aliases': {},
                'contacts': {},
            }
        )
        update_profile(profile, anon_profile)
        return anon_profile
