.PHONY: help install install-dev test lint format type-check clean docs serve-docs

help:
	@echo "PolicyGraph Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install package in production mode"
	@echo "  make install-dev      Install package with development dependencies"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test             Run all tests"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make lint             Check code with ruff"
	@echo "  make format           Format code with black and ruff"
	@echo "  make type-check       Type check with mypy"
	@echo "  make quality          Run all quality checks (lint, type-check, test)"
	@echo ""
	@echo "Development:"
	@echo "  make clean            Remove build artifacts and cache"
	@echo "  make pre-commit-init  Install pre-commit hooks"
	@echo "  make docs             Build documentation"
	@echo ""
	@echo "Training & Evaluation:"
	@echo "  make train            Train model (requires config.yaml)"
	@echo "  make evaluate         Evaluate trained model"
	@echo ""

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install pre-commit ruff black mypy

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=policygraph --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report: htmlcov/index.html"

lint:
	@echo "Linting with ruff..."
	ruff check policygraph tests scripts
	@echo "✓ Lint passed"

format:
	@echo "Formatting with black..."
	black policygraph tests scripts
	@echo "Fixing with ruff..."
	ruff check --fix policygraph tests scripts
	@echo "✓ Formatting complete"

type-check:
	@echo "Type checking with mypy..."
	mypy policygraph --ignore-missing-imports
	@echo "✓ Type check passed"

quality: lint type-check test
	@echo ""
	@echo "=================================="
	@echo "✓ All quality checks passed!"
	@echo "=================================="

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage *.egg-info
	@echo "✓ Clean complete"

pre-commit-init:
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

docs:
	@echo "Building documentation..."
	@echo "Documentation files are in docs/"
	@ls -la docs/

train:
	python -m policygraph.pipeline --train --config config.yaml

evaluate:
	python -m policygraph.pipeline --evaluate --config config.yaml

# Development targets
dev-server:
	@echo "Use: python -m http.server 8000 in docs/ directory"

repl:
	python

# CI/CD simulation
ci: clean install-dev quality
	@echo ""
	@echo "=================================="
	@echo "✓ CI checks passed!"
	@echo "=================================="
