#!/usr/bin/env python
# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import json
import typing as typ
import logging
import pathlib as pl

import fastapi
import fastapi.responses as resp
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from . import env

logger = logging.getLogger("guarantor.web_app")

DIR = pl.Path(__file__).parent

app = fastapi.FastAPI()
app.mount("/static", StaticFiles(directory=DIR / "static"), name="static")

templates = Jinja2Templates(directory=DIR / "templates")

Context = typ.NewType('Context', dict[str, typ.Any])


SUPPORTED_LANGUAGES = {'en', 'de'}


def _load_i18n(lang: str) -> dict[str, str]:
    i18n_dir = DIR / "static" / "i18n"

    with (i18n_dir / "en.json").open(encoding="utf-8") as fobj:
        i18n = json.load(fobj)

    if lang != 'en':
        with (i18n_dir / f"{lang}.json").open(encoding="utf-8") as fobj:
            i18n.update(json.load(fobj))

    return i18n


def _init_context(request: fastapi.Request) -> Context:
    lang = 'en'
    for accept_lang in request.headers.get('accept-language', 'en').split(","):
        if accept_lang in SUPPORTED_LANGUAGES:
            lang = accept_lang

    return Context(
        {
            'request': request,
            'lang'   : lang,
            'i18n'   : _load_i18n(lang),
            'static' : "/static",
            'debug'  : env.DEBUG_STATIC,
        }
    )


def render(template_filename: str, ctx: Context) -> templates.TemplateResponse:
    return templates.TemplateResponse(template_filename, ctx)


@app.get("/")
def home(request: fastapi.Request):
    return render("main.html", ctx=_init_context(request))
