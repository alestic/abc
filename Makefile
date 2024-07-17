# Makefile for abc (AI Bash Command)

# Variables
PYTHON := python3
INSTALL_DIR := $(HOME)/.local/bin
CONFIG_FILE := $(HOME)/.abc.conf
SHELL := /bin/bash

# Files
SCRIPT_FILES := abc_generate abc.sh
CONFIG_TEMPLATE := abc.conf.template

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help build install uninstall clean config

help: ## Display this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Install dependencies
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install --user -r requirements.txt

install: build ## Install abc_generate and abc.sh
	@echo "Installing abc..."
	mkdir -p $(INSTALL_DIR)
	cp $(SCRIPT_FILES) $(INSTALL_DIR)/
	chmod +x $(INSTALL_DIR)/abc_generate
	@echo "abc has been installed to $(INSTALL_DIR)"
	@echo ""
	@echo "Next steps:"
	@echo "1. Ensure $(INSTALL_DIR) is in your PATH"
	@echo "2. Add this line to your ~/.bashrc or ~/.zshrc:"
	@echo "   source \"$(INSTALL_DIR)/abc.sh\""
	@echo "3. Create $(CONFIG_FILE) using $(CONFIG_TEMPLATE) as a template"
	@echo "4. Reload your shell configuration"

uninstall: ## Uninstall abc
	@echo "Uninstalling abc..."
	rm -f $(addprefix $(INSTALL_DIR)/,$(SCRIPT_FILES))
	@echo "Removed abc_generate and abc.sh"
	@echo "Remember to remove the 'source' line from your shell configuration file"

clean: ## Remove generated files and caches
	@echo "Cleaning up..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

config: ## Create a config file from the template
	@if [ ! -f $(CONFIG_FILE) ]; then \
		cp $(CONFIG_TEMPLATE) $(CONFIG_FILE); \
		echo "Config file created at $(CONFIG_FILE)"; \
		echo "Please edit it with your API key"; \
	else \
		echo "Config file already exists at $(CONFIG_FILE)"; \
	fi