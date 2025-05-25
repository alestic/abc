"""Tests for the AWS Bedrock LLM provider."""

import json
import pytest
from unittest.mock import Mock, patch
import botocore.exceptions

from abc_provider_aws_bedrock.llm_provider import (
    AWSBedrockProvider,
    PROVIDER_NAME,
    DEFAULT_MODEL,
    DEFAULT_REGION,
)

# Test configuration
MOCK_CONFIG = {
    "provider": PROVIDER_NAME,
    "profile": "abc-cli",
}

MOCK_CONFIG_FULL = {
    "provider": PROVIDER_NAME,
    "profile": "abc-cli",
    "model": "anthropic.claude-sonnet-4-20250514-v1:0",
    "region": "us-east-1",
    "temperature": "0.5",
    "max_tokens": "500",
}

def test_init_wrong_provider():
    """Test provider initialization fails with wrong provider."""
    config = MOCK_CONFIG.copy()
    config["provider"] = "openai"
    with pytest.raises(ValueError, match=f"Provider must be '{PROVIDER_NAME}'"):
        AWSBedrockProvider(config)

def test_init_missing_provider():
    """Test provider initialization fails without provider field."""
    config = MOCK_CONFIG.copy()
    del config["provider"]
    with pytest.raises(ValueError, match=f"Provider must be '{PROVIDER_NAME}'"):
        AWSBedrockProvider(config)

def test_init_minimal_config():
    """Test provider initialization with minimal config."""
    with patch('boto3.Session') as mock_session:
        provider = AWSBedrockProvider(MOCK_CONFIG)
        assert provider.model_id == DEFAULT_MODEL
        assert provider.region == DEFAULT_REGION
        assert provider.temperature == 0.0
        assert provider.max_tokens == 1000
        assert provider.top_k is None

        # Verify boto3 session was created correctly
        mock_session.assert_called_once_with(
            region_name=DEFAULT_REGION,
            profile_name="abc-cli"
        )

def test_init_full_config():
    """Test provider initialization with full config."""
    with patch('boto3.Session') as mock_session:
        provider = AWSBedrockProvider(MOCK_CONFIG_FULL)
        assert provider.model_id == "anthropic.claude-sonnet-4-20250514-v1:0"
        assert provider.region == "us-east-1"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 500
        assert provider.top_k is None

        # Verify boto3 session was created correctly
        mock_session.assert_called_once_with(
            region_name="us-east-1",
            profile_name="abc-cli"
        )

def test_get_config_schema():
    """Test config schema is valid and complete."""
    with patch('boto3.Session'):
        provider = AWSBedrockProvider(MOCK_CONFIG)
    schema = provider.get_config_schema()

    assert isinstance(schema, dict)
    assert "provider" in schema["properties"]
    assert "profile" in schema["properties"]
    assert "region" in schema["properties"]
    assert "model" in schema["properties"]
    assert "top_k" in schema["properties"]
    assert schema["required"] == ["provider"]
    assert schema["properties"]["provider"]["enum"] == [PROVIDER_NAME]

def test_generate_command(mock_bedrock_client):
    """Test command generation with mocked Bedrock client."""
    provider = AWSBedrockProvider(MOCK_CONFIG)
    result = provider.generate_command(
        description="list files",
        context={"shell": "bash"},
        system_prompt="You are a CLI assistant"
    )

    # Verify result
    assert "echo test" in result
    assert "##DANGERLEVEL=0##" in result

    # Verify Bedrock client was called correctly
    mock_client = mock_bedrock_client.return_value.client.return_value
    mock_client.converse.assert_called_once()
    call_kwargs = mock_client.converse.call_args.kwargs
    assert call_kwargs["modelId"] == DEFAULT_MODEL

    # Verify request parameters
    assert call_kwargs["system"][0]["text"] == "You are a CLI assistant"
    assert call_kwargs["inferenceConfig"]["temperature"] == 0.0
    assert call_kwargs["inferenceConfig"]["maxTokens"] == 1000
    assert "list files" in call_kwargs["messages"][0]["content"][0]["text"]
    # By default, additionalModelRequestFields should not be present
    assert "additionalModelRequestFields" not in call_kwargs

def test_with_top_k():
    """Test command generation with top_k parameter."""
    config = MOCK_CONFIG.copy()
    config["top_k"] = "200"

    with patch('boto3.Session') as mock_session:
        provider = AWSBedrockProvider(config)
        assert provider.top_k == 200

        # Mock the converse response
        mock_client = mock_session.return_value.client.return_value
        mock_client.converse.return_value = {
            'output': {
                'message': {
                    'content': [{'text': "test command"}]
                }
            }
        }

        # Generate command
        provider.generate_command(
            description="test",
            context={"shell": "bash"},
            system_prompt="test prompt"
        )

        # Verify additionalModelRequestFields is included with top_k
        call_kwargs = mock_client.converse.call_args.kwargs
        assert "additionalModelRequestFields" in call_kwargs
        assert call_kwargs["additionalModelRequestFields"]["top_k"] == 200

def test_generate_command_api_error(mock_bedrock_client):
    """Test error handling when API call fails."""
    # Setup mock to raise exception
    mock_client = mock_bedrock_client.return_value.client.return_value
    mock_client.converse.side_effect = botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid request"
            }
        },
        operation_name="InvokeModel"
    )

    provider = AWSBedrockProvider(MOCK_CONFIG)
    with pytest.raises(RuntimeError, match="Bedrock API error"):
        provider.generate_command(
            description="list files",
            context={"shell": "bash"},
            system_prompt="You are a CLI assistant"
        )

def test_invalid_temperature():
    """Test provider initialization fails with invalid temperature."""
    config = MOCK_CONFIG.copy()
    config["temperature"] = "invalid"
    with patch('boto3.Session'):
        with pytest.raises(ValueError):
            AWSBedrockProvider(config)

def test_invalid_max_tokens():
    """Test provider initialization fails with invalid max_tokens."""
    config = MOCK_CONFIG.copy()
    config["max_tokens"] = "invalid"
    with patch('boto3.Session'):
        with pytest.raises(ValueError):
            AWSBedrockProvider(config)

def test_invalid_top_k():
    """Test provider initialization fails with invalid top_k."""
    config = MOCK_CONFIG.copy()
    config["top_k"] = "invalid"
    with patch('boto3.Session'):
        with pytest.raises(ValueError):
            AWSBedrockProvider(config)
