# Makefile for abc (AI bash/zsh/tcsh Command)

# Variables
PYTHON := python3
CONFIG_FILE := $(HOME)/.abc.conf
SHELL := /bin/bash
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# [Created with AI: Codex with GPT-6 Astra]
MODELS ?= claude-opus-4-5 claude-sonnet-5
REPEAT ?= 1
ABC_SECTION ?=
ABC_OPENAI_SECTION ?=
MAX_TOKENS ?= 4096
CASES ?=
export MODELS REPEAT ABC_SECTION ABC_OPENAI_SECTION MAX_TOKENS CASES

.PHONY: eval-image
eval-image: ## Build the isolated command evaluation image
	docker build -t abc-eval-fixtures:2 evals/fixtures

.PHONY: eval eval-view eval-smoke eval-summary
eval: ## Compare live models (MODELS="model-a model-b" REPEAT=1)
	@$(VENV_PYTHON) evals/run.py eval

eval-view: ## Open the local model comparison viewer
	@$(VENV_PYTHON) evals/run.py view

eval-smoke: ## Check eval integration without model API calls
	@$(VENV_PYTHON) evals/run.py eval --smoke

eval-summary: ## Show saved pass counts and response times without API calls
	@$(VENV_PYTHON) evals/summary.py

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
	@if ! command -v pipx &> /dev/null; then \
		echo "pipx is not installed. Please install it using your system package manager:"; \
		echo "  Ubuntu/Debian: sudo apt install pipx"; \
		echo "  macOS: brew install pipx"; \
		echo "  Other: python3 -m pip install --user pipx"; \
		exit 1; \
	fi
	@$(PYTHON) -m pipx ensurepath

.PHONY: install
install: install-pipx ## Install abc with all providers
	@echo "Installing abc using pipx..."
	@$(PYTHON) -m pipx install --force .
	@echo "Installing providers..."
	@$(PYTHON) -m pipx inject abc-cli ./abc_provider_anthropic
	@$(PYTHON) -m pipx inject abc-cli ./abc_provider_aws_bedrock
	@$(PYTHON) -m pipx inject abc-cli ./abc_provider_openai
	@abc_setup

.PHONY: install-dev
install-dev: install-pipx ## Install abc in development mode (editable)
	@echo "Installing abc in development mode..."
	@$(PYTHON) -m pipx install --force -e .
	@echo "Installing providers in development mode..."
	@$(PYTHON) -m pipx inject abc-cli -e ./abc_provider_anthropic
	@$(PYTHON) -m pipx inject abc-cli -e ./abc_provider_aws_bedrock
	@$(PYTHON) -m pipx inject abc-cli -e ./abc_provider_openai
	@abc_setup

.PHONY: install-nix
install-nix: ## Install abc using Nix
	@echo "Installing abc using Nix..."
	@nix profile install .
	@abc_setup

.PHONY: uninstall-nix
uninstall-nix: ## Uninstall abc from Nix profile
	@echo "Uninstalling abc from Nix profile..."
	@abc_setup --uninstall
	@nix profile remove abc

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
