"""AWS Bedrock LLM provider implementation."""

import json
import logging
import boto3
from typing import Dict, Any

logger = logging.getLogger(__name__)

from abc_cli import LLMProvider

PROVIDER_NAME = 'aws-bedrock'
DEFAULT_MODEL = 'anthropic.claude-sonnet-4-20250514-v1:0'
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1000
DEFAULT_REGION = 'us-east-1'
DEFAULT_TOP_K = None  # No top_k by default

class AWSBedrockProvider(LLMProvider):
    """AWS Bedrock LLM provider."""

    def __init__(self, config: Dict[str, str]):
        """Initialize provider with configuration.

        Args:
            config: Provider configuration from abc.conf
        """
        provider = config.get('provider')
        if provider != PROVIDER_NAME:
            raise ValueError(f"Provider must be '{PROVIDER_NAME}', got '{provider}'")

        self.model_id = config.get('model', DEFAULT_MODEL)
        self.region = config.get('region', DEFAULT_REGION)
        self.temperature = float(config.get('temperature', DEFAULT_TEMPERATURE))
        self.max_tokens = int(config.get('max_tokens', DEFAULT_MAX_TOKENS))

        # Parse top_k if provided
        top_k = config.get('top_k')
        self.top_k = int(top_k) if top_k is not None else DEFAULT_TOP_K

        # Use standard boto3 authentication
        self.session = boto3.Session(
            region_name=self.region,
            profile_name=config.get('profile')
        )
        self.bedrock = self.session.client('bedrock-runtime')

    def generate_command(
        self,
        description: str,
        context: Dict[str, Any],
        system_prompt: str,
    ) -> str:
        """Generate command using AWS Bedrock."""
        # Format request for Converse API
        request_body = {
            "inferenceConfig": {
                "maxTokens": self.max_tokens,
                "temperature": self.temperature
            },
            "system": [
                {
                    "text": system_prompt
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"Description: {description}\n\n{context.get('shell', 'bash').capitalize()} command(s):"
                        }
                    ]
                }
            ]
        }

        # Only add additionalModelRequestFields if top_k is specified
        if self.top_k is not None:
            request_body["additionalModelRequestFields"] = {
                "top_k": self.top_k
            }

        try:
            # Build API call parameters
            api_params = {
                "modelId": self.model_id,
                "messages": request_body["messages"],
                "system": request_body["system"],
                "inferenceConfig": request_body["inferenceConfig"]
            }

            # Only include additionalModelRequestFields if present
            if "additionalModelRequestFields" in request_body:
                api_params["additionalModelRequestFields"] = request_body["additionalModelRequestFields"]

            response = self.bedrock.converse(**api_params)

            # Log token usage at debug level
            if 'usage' in response:
                usage = response['usage']
                logger.debug(f"Token usage - Input: {usage['inputTokens']}, Output: {usage['outputTokens']}, Total: {usage['totalTokens']}")
                if 'stopReason' in response:
                    logger.debug(f"Stop reason: {response['stopReason']}")

            # Extract text from the assistant's response
            return response['output']['message']['content'][0]['text'].strip()

        except Exception as e:
            # Only wrap API errors, not validation errors
            raise RuntimeError(f"Bedrock API error: {str(e)}") from e

    def get_config_schema(self) -> Dict:
        """Get JSON schema for configuration."""
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Provider identifier (must be 'aws-bedrock')",
                    "enum": [PROVIDER_NAME]
                },
                "model": {
                    "type": "string",
                    "description": "Bedrock model ID",
                    "default": DEFAULT_MODEL
                },
                "region": {
                    "type": "string",
                    "description": "AWS region",
                    "default": DEFAULT_REGION
                },
                "profile": {
                    "type": "string",
                    "description": "AWS credential profile name (optional)"
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
                },
                "top_k": {
                    "type": "string",
                    "description": "Top-k parameter for sampling (optional)",
                }
            },
            "required": ["provider"]  # No api_key required - using AWS credentials
        }
