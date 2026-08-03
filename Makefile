.PHONY: lint typecheck security complexity test test-unit test-e2e coverage quality precommit setup

SRC := src/arclith_sample
UV  := uv run --frozen

setup:
	git config core.hooksPath .githooks

lint:
	$(UV) python -m ruff check $(SRC)

typecheck:
	$(UV) python -m mypy $(SRC)

security:
	$(UV) python -m bandit -r $(SRC) -ll

complexity:
	@output=$$($(UV) python -m radon cc $(SRC) --min C -s); \
	if [ -n "$$output" ]; then echo "$$output"; exit 1; fi

test:
	$(UV) python -m pytest -v

test-unit:
	$(UV) python -m pytest -v -m "not e2e"

test-e2e:
	$(UV) python -m pytest -v -m "e2e"

coverage:
	$(UV) python -m pytest --cov --cov-report=term-missing --cov-report=html

quality: lint security complexity typecheck coverage

precommit: lint typecheck security
