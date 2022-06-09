# This file is part of the guarantor project
# https://github.com/xkudev/guarantor
#
# Copyright (c) 2022 xkudev (xkudev@pm.me) - MIT License
# SPDX-License-Identifier: MIT

import pydantic


class UnsignedIdentity(pydantic.BaseModel):
    pass


class SignedIdentity(pydantic.BaseModel):
    pass
