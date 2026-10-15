PYTHON ?= python
.PHONY: preflight test-harness lint regress
preflight:
	$(PYTHON) -B scripts/preflight.py
test-harness:
	$(PYTHON) -B scripts/test_harness.py
lint:
	$(PYTHON) -B scripts/verify.py lint
regress:
	$(PYTHON) -B scripts/verify.py regress
