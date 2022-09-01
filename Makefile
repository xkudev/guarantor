
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
.PHONY: serve_api
serve_api:
	ENV=$${ENV-dev} \
		PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		PATH=$(DEV_ENV)/bin:$$PATH \
		$(DEV_ENV_PY) -m uvicorn guarantor.node_app:app --reload


## Serve API in development mode
.PHONY: serve_api_prod
serve_api_prod:
	$(DEV_ENV_PY) -m uvicorn guarantor.node_app:app


## Serve WebApp in development mode
.PHONY: serve_app
serve_app:
	ENV=$${ENV-dev} \
		PYTHONPATH=src/:vendor/:$$PYTHONPATH \
		GUARANTOR_DEBUG_STATIC=1 \
		PATH=$(DEV_ENV)/bin:$$PATH \
		$(DEV_ENV_PY) -m uvicorn guarantor.web_app:app --reload


## Serve API in development mode
.PHONY: serve_app
serve_app_prod:
	$(DEV_ENV_PY) -m uvicorn guarantor.web_app:app



.PHONY: chitchat
chitchat:
	GUARANTOR_URLS="http://127.0.0.1:8000" \
		guarantor chat --topic default-topic --message "hello world"


src/guarantor/static/img/logo_24.png: src/guarantor/static/img/logo.svg
	rsvg-convert -w 24 -h 24 src/guarantor/static/img/logo.svg -o $@


src/guarantor/static/img/logo_48.png: src/guarantor/static/img/logo.svg
	rsvg-convert -w 48 -h 48 src/guarantor/static/img/logo.svg -o $@
