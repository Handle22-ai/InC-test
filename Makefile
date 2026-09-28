PYTHON := .venv/bin/python
QUALITY_SCOPE := classifier.py harness rebuilt submission tests
.DEFAULT_GOAL := help

unexport TASK OUTPUT LIVE MAX_CALLS SPEC BASE
MAKEOVERRIDES :=

# Simple variables capture literal values once; recipe text never contains user values.
export HARNESS_SPEC := $(value SPEC)
export HARNESS_BASE := $(value BASE)
export HARNESS_TASK := $(value TASK)
export HARNESS_OUTPUT := $(value OUTPUT)
export HARNESS_LIVE := $(value LIVE)
export HARNESS_MAX_CALLS := $(value MAX_CALLS)
export HARNESS_BOOTSTRAP_PYTHON := $(value BOOTSTRAP_PYTHON)

.PHONY: help setup require-env check format test compile context gate consequences preflight evaluate-inherited e2e-live
help:
	@echo 'Offline: make setup | check | compile | gate | consequences SPEC=proposal.md BASE=spec.md | context TASK=recommendation-classification-maintenance'
	@echo 'Inherited system (live model calls): make preflight | evaluate-inherited | e2e-live  LIVE=1 MAX_CALLS=N'
	@echo 'CI: .venv/bin/python -B -m harness gate; only exit 0 passes. Make collapses nonzero exits to 2.'

setup:
	sh submission/setup.sh

require-env:
	@test -x "$(PYTHON)" || { echo 'Project environment missing: run make setup'; exit 1; }
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 14) else "Run make setup with Python >=3.14")'
	@$(PYTHON) -c 'import dotenv, yaml' || { echo 'Project dependencies missing: run make setup'; exit 1; }

check: require-env
	@$(PYTHON) -c 'import ruff, mypy' || { echo 'Quality tools missing: run make setup'; exit 1; }
	$(PYTHON) -m ruff format --check --no-cache $(QUALITY_SCOPE)
	$(PYTHON) -m ruff check --no-cache $(QUALITY_SCOPE)
	$(PYTHON) -m mypy --cache-dir=/dev/null
	$(PYTHON) -B -m harness.offline test

format: require-env
	$(PYTHON) -m ruff format --no-cache $(QUALITY_SCOPE)

test: require-env
	$(PYTHON) -B -m harness.offline test

compile: require-env
	$(PYTHON) -B -m harness compile

context gate consequences preflight evaluate-inherited e2e-live: require-env
	$(PYTHON) -B -m harness.commands $@
