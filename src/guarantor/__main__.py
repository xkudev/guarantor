#!/usr/bin/env python
# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import click

import guarantor

try:
    import pretty_traceback

    pretty_traceback.install()
except ImportError:
    pass  # no need to fail because of missing dev dependency

click.disable_unicode_literals_warning = True  # type: ignore[attr-defined]


@click.group()
def cli() -> None:
    """CLI for guarantor."""


@cli.command()
@click.version_option(version="2022.1001-alpha")
def version() -> None:
    """Show version number."""
    print(f"guarantor version: {guarantor.__version__}")
