"""Anthropic LLM provider implementation."""

import anthropic
from typing import Dict, Any

from abc_cli import LLMProvider

DEFAULT_MODEL = 'claude-sonnet-4-20250514'
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1000

class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""

    def __init__(self, config: Dict[str, str]):
        """Initialize provider with configuration.

        Args:
            config: Provider configuration from abc.conf
        """
        if config.get('provider') != 'anthropic':
            raise ValueError("Provider must be 'anthropic'")

        self.api_key = config['api_key']
        self.model = config.get('model', DEFAULT_MODEL)
        self.temperature = float(config.get('temperature', DEFAULT_TEMPERATURE))
        self.max_tokens = int(config.get('max_tokens', DEFAULT_MAX_TOKENS))
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_command(
        self,
        description: str,
        context: Dict[str, Any],
        system_prompt: str,
    ) -> str:
        """Generate command using Anthropic Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Description: {description}\n\n{context.get('shell', 'bash').capitalize()} command(s):"
                        }
                    ]
                }
            ]
        )
        return message.content[0].text.strip()

    def get_config_schema(self) -> Dict:
        """Get JSON schema for configuration."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Provider identifier (must be 'anthropic')",
                    "enum": ["anthropic"]
                },
                "api_key": {
                    "type": "string",
                    "description": "Anthropic API key"
                },
                "model": {
                    "type": "string",
                    "description": "Claude model to use",
                    "default": DEFAULT_MODEL
                },
                "temperature": {
                    "type": "string",
                    "description": "Sampling temperature",
                    "default": DEFAULT_TEMPERATURE
                },
                "max_tokens": {
                    "type": "string",
                    "description": "Maximum tokens in response",
                    "default": DEFAULT_MAX_TOKENS
                }
            },
            "required": ["provider", "api_key"]
        }
