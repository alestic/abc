"""OpenAI LLM provider implementation.

[Created by AI: Claude Code, Codex with GPT-6 Astra]
"""

import openai
from typing import Dict, Any

from abc_cli import LLMProvider

DEFAULT_MODEL = 'gpt-5'
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TIMEOUT = 120
DEFAULT_REASONING_EFFORT = 'minimal'  # Minimize reasoning tokens for simple command generation

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, config: Dict[str, str]):
        """Initialize provider with configuration.

        Args:
            config: Provider configuration from abc.conf
        """
        if config.get('provider') != 'openai':
            raise ValueError("Provider must be 'openai'")

        self.api_key = config['api_key']
        self.model = config.get('model', DEFAULT_MODEL)
        self.temperature = float(config.get('temperature', DEFAULT_TEMPERATURE))
        self.max_tokens = int(config.get('max_tokens', DEFAULT_MAX_TOKENS))
        self.timeout = float(config.get('timeout', DEFAULT_TIMEOUT))
        self.reasoning_effort = config.get('reasoning_effort', DEFAULT_REASONING_EFFORT)
        self.api = config.get('api', 'chat_completions')
        if self.api not in ('chat_completions', 'responses'):
            raise ValueError('api must be chat_completions or responses')
        self.responses_effort = config.get('reasoning_effort')
        
        # Optional organization ID
        self.organization = config.get('organization')
        
        # Initialize OpenAI client
        client_kwargs = {
            'api_key': self.api_key,
            'timeout': self.timeout
        }
        
        if self.organization:
            client_kwargs['organization'] = self.organization
            
        self.client = openai.OpenAI(**client_kwargs)

    def generate_command(
        self,
        description: str,
        context: Dict[str, Any],
        system_prompt: str,
    ) -> str:
        """Generate command using OpenAI GPT models."""
        try:
            if self.api == 'responses':
                params = {
                    'model': self.model,
                    'instructions': system_prompt,
                    'input': f"Description: {description}\n\n{context.get('shell', 'bash').capitalize()} command(s):",
                    'max_output_tokens': self.max_tokens,
                    'store': False,
                }
                if self.responses_effort:
                    params['reasoning'] = {'effort': self.responses_effort}
                if self.temperature != 0.0:
                    params['temperature'] = self.temperature
                response = self.client.responses.create(**params)
                if response.status != 'completed':
                    raise ValueError('OpenAI response did not complete; check max_tokens and model settings')
                if not response.output_text.strip():
                    raise ValueError('OpenAI returned no text command')
                return response.output_text.strip()
            # Build request parameters
            request_params = {
                "model": self.model,
                "max_completion_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": f"Description: {description}\n\n{context.get('shell', 'bash').capitalize()} command(s):"
                    }
                ]
            }
            
            # Add reasoning_effort for GPT-5 models
            if 'gpt-5' in self.model.lower():
                request_params["reasoning_effort"] = self.reasoning_effort
            
            # Only add temperature if it's not the default 0.0 (some models don't support 0.0)
            if self.temperature != 0.0:
                request_params["temperature"] = self.temperature
                
            response = self.client.chat.completions.create(**request_params)
            
            # Debug logging
            import logging
            logging.debug(f"OpenAI response: {response}")
            logging.debug(f"Response choices: {response.choices}")
            if response.choices:
                logging.debug(f"First choice: {response.choices[0]}")
                logging.debug(f"Message: {response.choices[0].message}")
                logging.debug(f"Content: {response.choices[0].message.content}")
            
            result = response.choices[0].message.content
            if result is None:
                logging.warning("OpenAI returned None content")
                return ""
            return result.strip()
        except openai.APIError as e:
            raise RuntimeError(f"OpenAI API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")

    def get_config_schema(self) -> Dict:
        """Get JSON schema for configuration."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Provider identifier (must be 'openai')",
                    "enum": ["openai"]
                },
                "api_key": {
                    "type": "string",
                    "description": "OpenAI API key"
                },
                "model": {
                    "type": "string",
                    "description": "OpenAI model to use",
                    "default": DEFAULT_MODEL,
                    "examples": ["gpt-5", "gpt-4o", "gpt-4-turbo"]
                },
                "temperature": {
                    "type": "string",
                    "description": "Sampling temperature (0.0-2.0)",
                    "default": str(DEFAULT_TEMPERATURE)
                },
                "max_tokens": {
                    "type": "string",
                    "description": "Maximum completion tokens in response (uses max_completion_tokens parameter)",
                    "default": str(DEFAULT_MAX_TOKENS)
                },
                "timeout": {
                    "type": "string",
                    "description": "Request timeout in seconds",
                    "default": str(DEFAULT_TIMEOUT)
                },
                "organization": {
                    "type": "string",
                    "description": "OpenAI organization ID (optional)"
                },
                "reasoning_effort": {
                    "type": "string",
                    "description": "Reasoning effort for GPT-5 models (minimal, low, medium, high)",
                    "default": DEFAULT_REASONING_EFFORT,
                    "enum": ["none", "minimal", "low", "medium", "high", "xhigh", "max"]
                },
                "api": {
                    "type": "string",
                    "enum": ["chat_completions", "responses"],
                    "default": "chat_completions"
                }
            },
            "required": ["provider", "api_key"]
        }
