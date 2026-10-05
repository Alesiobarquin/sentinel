PYTHON ?= .venv/bin/python
QUERY ?= count({__name__!=""})
SCENARIO ?= payment-failure
export QUERY SCENARIO

.PHONY: setup help doctor demo-fetch demo-config demo-up demo-down demo-status demo-verify metrics metric-names services lab-inject lab-reset login models first-investigation scenario-validate kind-up kind-credentials kind-verify kind-down pods test check check-live-telemetry check-live-kubernetes

setup:
	uv sync --frozen

login:
	$(PYTHON) -m sentinel login

models:
	$(PYTHON) -m sentinel models

first-investigation:
	$(PYTHON) scripts/first_investigation.py

scenario-validate:
	$(PYTHON) scripts/validate_scenarios.py

kind-up:
	$(PYTHON) scripts/kind_lab.py up

kind-credentials:
	$(PYTHON) scripts/kind_lab.py credentials

kind-verify:
	$(PYTHON) scripts/kind_lab.py verify

kind-down:
	$(PYTHON) scripts/kind_lab.py down

pods:
	$(PYTHON) -m sentinel pods --service fixture

help:
	@$(PYTHON) scripts/demo.py --help
	@$(PYTHON) -m sentinel --help

doctor:
	$(PYTHON) scripts/demo.py doctor

demo-fetch:
	$(PYTHON) scripts/demo.py fetch

demo-config:
	$(PYTHON) scripts/demo.py config

demo-up:
	$(PYTHON) scripts/demo.py up

demo-down:
	$(PYTHON) scripts/demo.py down

demo-status:
	$(PYTHON) scripts/demo.py status

demo-verify:
	$(PYTHON) scripts/demo.py verify

metrics:
	$(PYTHON) -m sentinel metrics --query "$$QUERY"

metric-names:
	$(PYTHON) -m sentinel metric-names

services:
	$(PYTHON) -m sentinel services

lab-inject:
	$(PYTHON) scripts/demo.py inject --scenario "$$SCENARIO"

lab-reset:
	$(PYTHON) scripts/demo.py reset

test:
	$(PYTHON) -m unittest discover -s tests -v

check-live-telemetry:
	SENTINEL_LIVE_TESTS=1 SENTINEL_K8_LIVE_TESTS=0 SENTINEL_LOG_INDEX='otel-logs*' SENTINEL_LOG_SCHEMA=infra/docker/log-schema.json $(PYTHON) -m unittest discover -s tests -p 'test_live_*.py' -v

check-live-kubernetes:
	SENTINEL_LIVE_TESTS=0 SENTINEL_K8_LIVE_TESTS=1 $(PYTHON) -m unittest discover -s tests -p test_live_kubernetes.py -v

check: test
	$(PYTHON) -m compileall -q sentinel scripts evals tests
