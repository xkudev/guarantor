import os
import sys
import time
import shutil
import typing as typ
import pathlib as pl
import subprocess as sp

import pytest
import click.testing

import guarantor.cli

CLI_ENV = {
    'GUARANTOR_CONNECT_URLS': "http://127.0.0.1:8000",
    'GUARANTOR_DB_URL'      : "sqlite:///./guarantor.sqlite3",
}


def text_env_defaults():
    assert CLI_ENV.keys() == guarantor.cli.cli.ENV_DEFAULTS_OPTIONS.keys()
    for key in CLI_ENV.keys():
        assert type(CLI_ENV[key]) == guarantor.cli.cli.ENV_DEFAULTS_OPTIONS[key]


def shell(*cmd):
    return sp.check_output(cmd, env=CLI_ENV)


class Context:
    def __init__(self, tmpdir: pl.Path) -> None:
        env = CLI_ENV.copy()
        env['PATH'] = os.environ['PATH']
        self.runner = click.testing.CliRunner(env=CLI_ENV)

    def cli(self, *argv):
        return self.runner.invoke(guarantor.cli.cli, argv)


@pytest.fixture
def ctx(tmpdir: pl.Path) -> typ.Iterator[Context]:
    """
    1. Create a director for server data (configuration and database)
    2. Swith to directory
    3. Start endpoint server
    """
    orig_cwd = os.getcwd()

    _debug = os.getenv('DEBUGTEST', "0") == "1"
    if _debug:
        tmpdir = pl.Path("..") / "test_server_data"
        if tmpdir.exists():
            time.sleep(0.2)
            shutil.rmtree(str(tmpdir))
        tmpdir.mkdir()

    os.chdir(str(tmpdir))

    ctx = Context(tmpdir)
    ctx.cli("serve", "--port=5151")
    print("???")

    yield ctx

    os.chdir(orig_cwd)

    if not _debug:
        shutil.rmtree(str(tmpdir))


def test_help(ctx: Context):
    res = ctx.cli('--help')
    assert res.exit_code == 0
    assert "--version" in result.output


def test_info(ctx: Context):
    result = ctx.cli.info()
    assert res.exit_code == 0
    print(res.output)
    assert False
