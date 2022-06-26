# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

import os
import json
import time
import shutil
import typing as typ
import pathlib as pl
import subprocess as sp

import pytest
import click.testing

import guarantor.cli

TEST_ENV_DEFAULTS = {
    'GUARANTOR_URLS'  : "http://localhost:8021",
    'GUARANTOR_HOST'  : "0.0.0.0",
    'GUARANTOR_PORT'  : "8021",
    'GUARANTOR_DB_URL': "sqlite:///./guarantor.sqlite3",
}


IS_IN_CI_CONTEXT = os.getenv('IS_IN_CI_CONTEXT') == "1"


def test_env_defaults():
    assert set(TEST_ENV_DEFAULTS) <= set(guarantor.cli.ENV_DEFAULTS_OPTIONS)
    for key, val in TEST_ENV_DEFAULTS.items():
        assert type(val) == type(guarantor.cli.ENV_DEFAULTS_OPTIONS[key])


def shell(*cmd):
    return sp.check_output(cmd, env=TEST_ENV_DEFAULTS)


def new_env(**overrides) -> dict[str, str]:
    env = TEST_ENV_DEFAULTS.copy()
    env['PATH'      ] = os.environ['PATH']
    env['PYTHONPATH'] = os.environ['PYTHONPATH']
    for key, val in overrides:
        env[key.upper()] = val
    return env


class Context:
    def __init__(self, tmpdir: pl.Path) -> None:
        self.cli_env = new_env()

    def cli(self, *argv):
        assert self.cli_env['GUARANTOR_URLS'] == "http://localhost:8021"
        runner = click.testing.CliRunner(env=self.cli_env)
        return runner.invoke(guarantor.cli.cli, list(argv))


@pytest.fixture(scope="module")
def server():
    serve_env = new_env()

    sp.run(["python", "-m", "alembic", "upgrade", "head"])

    capture_serve_output = os.getenv("CAPTURE_SERVE_OUTPUT", "1") == "1"
    serve_cmd            = ["python", "-m", "guarantor", "serve", "--no-reload"]

    if capture_serve_output:
        proc = sp.Popen(serve_cmd, env=serve_env, stdout=sp.PIPE, stderr=sp.PIPE)
    else:
        proc = sp.Popen(serve_cmd, env=serve_env)

    with proc:
        time.sleep(3.0)
        try:
            yield proc
        finally:
            proc.kill()
            time.sleep(1.0)


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
    yield ctx

    os.chdir(orig_cwd)

    if not _debug:
        shutil.rmtree(str(tmpdir))


def test_help(ctx: Context):
    res = ctx.cli('--help')
    assert res.exit_code == 0
    assert "--version" in res.output


@pytest.mark.skipif(IS_IN_CI_CONTEXT, reason="HTTP server doesn't want to start on CI")
def test_info(ctx: Context, server: sp.Popen):
    res = ctx.cli("info")
    assert res.exit_code == 0
    server_info = json.loads(res.output)
    assert set(server_info.keys()) >= {'name', 'version', 'time', 'iso8601'}
