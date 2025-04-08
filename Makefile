.PHONY: install clean lint format test coverage build

install:
	pip install -e ".[dev]"

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

coverage:
	pytest --cov=src/sidekick --cov-report=term --cov-report=html

build:
	python -m build
