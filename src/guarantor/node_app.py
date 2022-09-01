#!/usr/bin/env python
# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT
import logging

import fastapi
import fastapi.responses as resp

logger = logging.getLogger("guarantor.node_app")

app = fastapi.FastAPI()
