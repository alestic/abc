# Makefile for abc (AI bash/zsh/tcsh Command)

# Variables
PYTHON := python3
CONFIG_FILE := $(HOME)/.abc.conf
SHELL := /bin/bash
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# Files
CONFIG_TEMPLATE := abc.conf.template

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install-pipx
install-pipx:
	@$(PYTHON) -m pip install --user --quiet pipx
	@$(PYTHON) -m pipx ensurepath

.PHONY: install
install: install-pipx ## Install abc
	@echo "Installing abc using pipx..."
	@$(PYTHON) -m pipx install --force .
	@abc_setup

.PHONY: setup
setup: ## Re-create the config file
	@abc_setup

.PHONY: uninstall
uninstall: ## Uninstall abc
	@echo "Uninstalling abc..."
	@abc_setup --uninstall
	@$(PYTHON) -m pipx uninstall abc-cli

.PHONY: tree
tree: ## Show a file tree
	@git ls-files | tree --fromfile -a --filesfirst

$(VENV)/bin/activate: ## Create virtual environment
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV)

$(VENV)/.test-deps: $(VENV)/bin/activate pyproject.toml
	@echo "Installing test dependencies..."
	@$(VENV_PIP) install -q -e ".[test]"
	@touch $@

.PHONY: test
test: $(VENV)/.test-deps ## Run tests (use COVERAGE=1 for coverage report)
	@echo "Running tests..."
	@if [ "$(COVERAGE)" = "1" ]; then \
		$(VENV_PYTHON) -m pytest --cov=abc_cli --cov-report=term-missing; \
	else \
		$(VENV_PYTHON) -m pytest; \
	fi

.PHONY: clean
clean: ## Clean all artifacts (Python cache, test artifacts, and virtual environment)
	@echo "Cleaning all artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -exec rm -f {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(VENV)
	@echo "Clean complete."
