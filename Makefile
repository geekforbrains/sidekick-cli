.PHONY: install clean lint format build test

install:
	pip install -e ".[dev]"

run:
	env/bin/sidekick

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	black src/
	isort src/
	flake8 src/

test:
	pytest

build:
	python -m build