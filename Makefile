# AgentSpec Development Makefile
# Provides common development tasks for testing, linting, formatting, and validation

.PHONY: help install install-dev test test-unit test-integration test-e2e lint format validate clean build pre-push check-all

# Default target
help:
	@echo "AgentSpec Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-unit    Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-e2e     Run end-to-end tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run linting (flake8, mypy)"
	@echo "  format       Format code (black, isort)"
	@echo "  validate     Validate AgentSpec configuration"
	@echo ""
	@echo "Development:"
	@echo "  clean        Clean build artifacts and cache"
	@echo "  build        Build package"
	@echo "  pre-push     Run all checks before pushing"
	@echo "  check-all    Run comprehensive checks"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e .[dev,test]

# Testing targets
test:
	python3 -m pytest tests/ -v --cov=agentspec --cov-report=term-missing

test-unit:
	python3 -m pytest tests/unit/ -v --cov=agentspec --cov-report=term-missing --cov-fail-under=0

test-integration:
	python3 -m pytest tests/integration/ -v --cov=agentspec --cov-report=term-missing --cov-fail-under=0

test-e2e:
	python3 -m pytest tests/e2e/ -v --cov=agentspec --cov-report=term-missing --cov-fail-under=0

test-fast:
	python3 -m pytest tests/ -x --tb=short

# Code quality targets
lint:
	@echo "Running flake8..."
	python3 -m flake8 agentspec/ tests/
	@echo "Running mypy..."
	python3 -m mypy agentspec/ --ignore-missing-imports

format:
	@echo "Running black..."
	python3 -m black agentspec/ tests/
	@echo "Running isort..."
	python3 -m isort agentspec/ tests/ --profile=black

format-check:
	@echo "Checking black formatting..."
	python3 -m black agentspec/ tests/ --check
	@echo "Checking isort formatting..."
	python3 -m isort agentspec/ tests/ --profile=black --check-only

# Validation targets
validate:
	@echo "Validating AgentSpec templates..."
	python3 -c "from agentspec.core.template_manager import TemplateManager; tm = TemplateManager(); templates = tm.load_templates(); print(f'✅ Loaded {len(templates)} templates successfully')"
	@echo "Validating AgentSpec instructions..."
	python3 -c "from agentspec.core.instruction_database import InstructionDatabase; idb = InstructionDatabase(); instructions = idb.load_instructions(); print(f'✅ Loaded {len(instructions)} instructions successfully')"

# Security checks
security:
	@echo "Running bandit security checks..."
	python3 -m bandit -r agentspec/ --skip B101,B603,B607

# Clean targets
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build targets
build: clean
	python3 -m build

# Pre-commit and pre-push checks
pre-commit:
	@echo "Running pre-commit checks..."
	make format-check
	make lint
	make test-fast

# Quick checks for the specific issues that failed in GitHub Actions
quick-security-lint:
	@echo "Running quick security and lint checks..."
	python3 -m bandit -r agentspec/ --skip B101,B603,B607 -q
	python3 -m flake8 agentspec/ tests/ --select=F541 --max-line-length=88
	@echo "✅ Security and critical lint checks passed!"

pre-push: clean
	@echo "Running comprehensive pre-push checks..."
	make format-check
	make lint
	make security
	make test
	make validate
	@echo "✅ All pre-push checks passed!"

# Comprehensive check target
check-all: clean
	@echo "Running all quality checks..."
	make format-check
	make lint
	make security
	make test
	make validate
	@echo "✅ All checks completed successfully!"

# Development workflow helpers
dev-setup: install-dev
	@echo "Setting up development environment..."
	pre-commit install
	@echo "✅ Development environment ready!"

quick-check:
	@echo "Running quick development checks..."
	make format
	make test-fast
	@echo "✅ Quick checks completed!"
