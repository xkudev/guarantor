import os

ENV_HOME        = os.environ['HOME']
XDG_CONFIG_HOME = os.getenv("XDG_CONFIG_HOME", os.path.join(ENV_HOME, ".config"))
XDG_DATA_HOME   = os.getenv("XDG_DATA_HOME"  , os.path.join(ENV_HOME, ".local", "share"))

DEFAULT_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "guarantor")
DEFAULT_DATA_DIR   = os.path.join(XDG_DATA_HOME  , "guarantor")

DEFAULT_DB_DIR = os.path.join(DEFAULT_DATA_DIR, "kvstore")
