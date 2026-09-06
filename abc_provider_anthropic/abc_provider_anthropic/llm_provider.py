"""Anthropic LLM provider implementation."""

import anthropic
from typing import Dict, Any

from abc_cli import LLMProvider

DEFAULT_MODEL = 'claude-opus-4-5'
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
        # Newer Claude models (Opus 4.7+, Sonnet 5, Fable 5) reject the
        # `temperature` parameter. Only send it when the user explicitly
        # configures one; otherwise omit it entirely.
        self.temperature = (
            float(config['temperature']) if 'temperature' in config else None
        )
        self.max_tokens = int(config.get('max_tokens', DEFAULT_MAX_TOKENS))
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_command(
        self,
        description: str,
        context: Dict[str, Any],
        system_prompt: str,
    ) -> str:
        """Generate command using Anthropic Claude."""
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": [
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
        }
        if self.temperature is not None:
            request_params["temperature"] = self.temperature

        message = self.client.messages.create(**request_params)
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
                    "description": "Sampling temperature (omitted unless set; unsupported by newer Claude models)"
                },
                "max_tokens": {
                    "type": "string",
                    "description": "Maximum tokens in response",
                    "default": DEFAULT_MAX_TOKENS
                }
            },
            "required": ["provider", "api_key"]
        }
