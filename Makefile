# Makefile for abc (AI Bash Command)

# Python interpreter to use
PYTHON := python3

# Installation directory (should be in PATH)
INSTALL_DIR := $(HOME)/.local/bin

# Config file location
CONFIG_FILE := $(HOME)/.abc.conf

# Default target
.DEFAULT_GOAL := help

.PHONY: help build install uninstall clean

# Target descriptions should start with a capital letter and not end with a period
help: ## Display this help message
	@echo "Usage: make [target]"
	@echo
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Install dependencies globally or in user space
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install --user -r requirements.txt

install: build ## Install the abc program and interactive script
	@echo "Installing abc..."
	mkdir -p $(INSTALL_DIR)
	cp abc $(INSTALL_DIR)/abc
	chmod +x $(INSTALL_DIR)/abc
	@echo "abc has been installed to $(INSTALL_DIR)/abc"
	@echo "Installing abc_interactive.sh..."
	cp abc_interactive.sh $(INSTALL_DIR)/abc_interactive.sh
	@echo "abc_interactive.sh has been installed to $(INSTALL_DIR)/abc_interactive.sh"
	@echo "Make sure $(INSTALL_DIR) is in your PATH"
	@echo
	@echo "To enable the interactive mode, add the following line to your ~/.bashrc:"
	@echo "source \"$(INSTALL_DIR)/abc_interactive.sh\""
	@echo
	@echo "Then, reload your shell configuration with:"
	@echo "source ~/.bashrc"

uninstall: ## Uninstall the abc program, interactive script, and remove the config file
	@echo "Uninstalling abc..."
	rm -f $(INSTALL_DIR)/abc
	rm -f $(INSTALL_DIR)/abc_interactive.sh
	rm -f $(CONFIG_FILE)
	@echo "abc has been uninstalled, the interactive script and config file have been removed"

clean: ## Remove generated files
	@echo "Cleaning up..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete