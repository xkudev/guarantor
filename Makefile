
PACKAGE_NAME := guarantor

# This is the python version that is used for:
# - `make fmt`
# - `make ipy`
# - `make lint`
# - `make devtest`
DEVELOPMENT_PYTHON_VERSION := python=3.10

# These must be valid (space separated) conda package names.
# A separate conda environment will be created for each of these.
#
# Some valid options are:
# - python=2.7
# - python=3.5
# - python=3.6
# - python=3.7
# - pypy2.7
# - pypy3.5
SUPPORTED_PYTHON_VERSIONS := python=3.10

include Makefile.bootstrapit.make

## -- Extra/Custom/Project Specific Tasks --

## Serve API in development mode
.PHONY: api_serve
api_serve:
	$(DEV_ENV_PY) -m uvicorn guarantor.app:app --reload


## Serve API in development mode
.PHONY: api_serve_prod
api_serve_prod:
	$(DEV_ENV_PY) -m uvicorn guarantor.app:app
