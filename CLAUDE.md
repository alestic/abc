# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

abc (AI Bash Command) is a command-line tool that translates natural language descriptions into shell commands using LLMs. It uses a plugin architecture to support multiple LLM providers.

## Architecture

### Core Components
- **abc_cli**: Main package containing command generation logic
  - `abc_generate.py`: CLI entry point that handles command generation
  - `llm_provider.py`: Abstract base class that all providers must implement
  - `abc_setup.py`: Installation script for shell integration
  - Shell scripts (`abc.sh`, `abc.tcsh`) provide the `abc` shell function

### Provider Plugins
- **abc_provider_anthropic**: Anthropic Claude provider
- **abc_provider_aws_bedrock**: AWS Bedrock provider
- Providers are discovered via Python entry points defined in pyproject.toml

### Key Design Patterns
1. The `abc` command is a shell function (not a direct Python script) that calls `abc_generate`
2. Providers implement the `LLMProvider` abstract base class
3. Configuration uses INI format with sections for different providers
4. Shell integration must be idempotent (safe to run multiple times)

## Development Commands

### Installation
```bash
# Development install
pipx install -e .
pipx inject abc-cli -e ./abc_provider_anthropic
pipx inject abc-cli -e ./abc_provider_aws_bedrock
abc_setup --no-prompt
```

### Testing
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=abc_cli

# Run specific test file
python -m pytest abc_cli/tests/test_abc_generate.py
```

### Uninstall
```bash
abc_setup --uninstall --no-prompt
pipx uninstall abc-cli
```

## Critical Implementation Details

1. **Python Compatibility**: Must support Python ≥ 3.8
2. **Shell Function**: The `abc` command users type is a shell function that:
   - Calls `abc_generate` with the user's description
   - Presents the generated command in an editable prompt
   - Adds executed commands to shell history
3. **Configuration Priority**:
   - Primary: `~/.config/abc/config` (XDG standard)
   - Legacy: `~/.abc.conf` (for backward compatibility)
4. **Danger Level Evaluation**: Commands are evaluated for potential harm before presentation
5. **Version Updates**: When releasing, update version in:
   - `pyproject.toml` (main package)
   - Provider packages' `pyproject.toml` files
   - Any version strings in the code

## Working with Providers

When implementing or modifying providers:
1. Inherit from `abc_cli.llm_provider.LLMProvider`
2. Implement required methods: `configure()`, `generate_command()`, `is_configured()`
3. Register via entry point in pyproject.toml
4. Support both environment variables and config file for API keys
5. Handle danger level evaluation in generated commands