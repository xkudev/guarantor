# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import os
import typing as typ

import click

OptionType = typ.Any

Option = typ.Any


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
