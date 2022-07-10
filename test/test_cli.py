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
import guarantor.schemas

TEST_ENV_DEFAULTS = {
    'GUARANTOR_URLS'  : "http://localhost:8021",
    'GUARANTOR_BIND'  : "0.0.0.0:8021",
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
    env['HOME'      ] = os.environ['HOME']
    env['PATH'      ] = os.environ['PATH']
    env['PYTHONPATH'] = os.environ['PYTHONPATH']
    for key, val in overrides:
        env[key.upper()] = val
    return env


class Context:
    def __init__(self, tmpdir: pl.Path) -> None:
        self.cli_env = new_env()

    def cli(self, *argv, **kwargs):
        assert self.cli_env['GUARANTOR_URLS'] == "http://localhost:8021"
        runner = click.testing.CliRunner(env=self.cli_env)
        return runner.invoke(
            guarantor.cli.cli, list(argv) + [f"--{k}={v}" for k, v in kwargs.items()], catch_exceptions=False
        )


@pytest.fixture(scope="module")
def server():
    capture_serve_output = os.getenv("CAPTURE_SERVE_OUTPUT", "0") == "1"

    serve_env = new_env()

    sp.run(["python", "-m", "alembic", "upgrade", "head"], check=True)
    serve_cmd = ["python", "-m", "guarantor", "serve", "--no-reload"]

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


@pytest.mark.skipif(IS_IN_CI_CONTEXT, reason="HTTP server doesn't want to start on CI")
def test_post_identity(ctx: Context, server: sp.Popen):
    res = ctx.cli(
        "post-identity", "L4gXBvYrXHo59HLeyem94D9yLpRkURCHmCwQtPuWW9m6o1X8p8sp", props='{"foo": "bar"}'
    )

    assert res.exit_code == 0

    identity_response = guarantor.schemas.IdentityResponse(**json.loads(res.output))

    assert identity_response.identity.address == '1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv'
    assert guarantor.schemas.verify_identity_envelope(identity_response.identity)
    assert identity_response.identity.document.props == {'foo': "bar"}
    assert identity_response.path == '/v1/identity/1LsPb3D1o1Z7CzEt1kv5QVxErfqzXxaZXv'


@pytest.mark.skipif(IS_IN_CI_CONTEXT, reason="HTTP server doesn't want to start on CI")
def test_post_identity_twice(ctx: Context, server: sp.Popen):

    # first post works

    res = ctx.cli(
        "post-identity", "5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss", props='{"foo": "bar"}'
    )

    assert res.exit_code == 0

    identity_response = guarantor.schemas.IdentityResponse(**json.loads(res.output))

    assert identity_response.identity.address == '1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN'
    assert guarantor.schemas.verify_identity_envelope(identity_response.identity)
    assert identity_response.identity.document.props == {'foo': "bar"}
    assert identity_response.path == '/v1/identity/1HZwkjkeaoZfTSaJxDw6aKkxp45agDiEzN'
    
    # second post fails with 409 status code
    with pytest.raises(Exception, match='.*409.*'):

        ctx.cli(
            "post-identity", "5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss", props='{"foo": "bar", "bam": "baz"}'
        )
