# Plugin Development Guide

This guide explains how to create new LLM provider plugins for abc-cli.

## Overview

abc-cli uses a plugin system that allows different LLM providers to be used for command generation. Each provider is a separate Python package that:

1. Implements the LLMProvider interface
2. Registers itself as an entry point
3. Provides configuration schema validation

## Creating a Provider Package

1. Create a new package directory:
```bash
mkdir abc-provider-NAME
cd abc-provider-NAME
```

2. Create the package structure:
```
abc-provider-NAME/
├── pyproject.toml
├── README.md
└── abc_provider_NAME/
    ├── __init__.py
    └── llm_provider.py
```

3. Configure pyproject.toml:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "abc-provider-NAME"
version = "2026.09.06.2"  # Match abc-cli version format
description = "NAME LLM provider for abc-cli"
readme = "README.md"
requires-python = ">=3.8"
license = "Apache-2.0"
dependencies = [
    "NAME-api-package>=X.Y.Z",  # Provider's API package
]

[project.entry-points."abc.llm_providers"]
NAME = "abc_provider_NAME.llm_provider:NAMEProvider"
```

## Implementing the Provider

Create a provider class in llm_provider.py that implements the LLMProvider interface:

```python
from abc_cli import LLMProvider
from typing import Dict, Any

class NAMEProvider(LLMProvider):
    """NAME LLM provider."""

    def __init__(self, config: Dict[str, str]):
        """Initialize provider with configuration."""
        if config.get('provider') != 'NAME':
            raise ValueError("Provider must be 'NAME'")

        self.api_key = config['api_key']
        # Initialize other provider-specific settings
        # Initialize API client

    def generate_command(
        self,
        description: str,
        context: Dict[str, Any],
        system_prompt: str,
    ) -> str:
        """Generate command using NAME's API."""
        # Call the provider's API to generate a command
        # Return the command with danger level annotation:
        # command
        # ##DANGERLEVEL=N## justification

    def get_config_schema(self) -> Dict:
        """Get JSON schema for configuration."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Provider identifier (must be 'NAME')",
                    "enum": ["NAME"]
                },
                "api_key": {
                    "type": "string",
                    "description": "NAME API key"
                },
                # Add other provider-specific settings
            },
            "required": ["provider", "api_key"]
        }
```

## Testing

1. Create a test suite:
```
abc-provider-NAME/
└── tests/
    ├── conftest.py
    └── test_provider.py
```

2. Add test dependencies to pyproject.toml:
```toml
[project.optional-dependencies]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```

3. Create tests that verify:
- Configuration parsing and validation
- Command generation functionality
- Error handling
- Integration with abc-cli core

## Installation

Users can install your provider using:
```bash
pipx inject abc-cli abc-provider-NAME
```

For development:
```bash
pipx inject abc-cli -e ./abc-provider-NAME
```

## Configuration

Users configure your provider in ~/.abc.conf:
```ini
[default]
provider = NAME
api_key = {NAME_API_KEY}
# Other provider-specific settings

[name1]  # Named configuration
provider = NAME
api_key = {NAME_API_KEY}
model = specific-model
```

## Best Practices

1. Error Handling:
   - Validate all configuration settings
   - Provide clear error messages
   - Handle API errors gracefully

2. Testing:
   - Mock API calls in tests
   - Test error conditions

3. Documentation:
   - Document all configuration options
   - Provide installation instructions
   - Include example configurations

4. Security:
   - Never log API keys or sensitive data
   - Validate and sanitize all inputs
   - Follow provider's security guidelines

## Example

See [abc_provider_anthropic](abc_provider_anthropic/) for a complete example of a provider implementation.

<!-- [Created with AI: Codex with GPT-6 Astra] -->
