"""Tests for the OpenAI LLM provider.

[Created by AI: Claude Code, Codex with GPT-6 Astra, Claude Code with Fable 5.1]
"""

import pytest
from unittest.mock import Mock, patch
import openai

from abc_provider_openai.llm_provider import OpenAIProvider, DEFAULT_MODEL

# Test configuration
MOCK_API_KEY = "test_api_key"
MOCK_CONFIG = {
    "provider": "openai",
    "api_key": MOCK_API_KEY,
}

MOCK_CONFIG_FULL = {
    "provider": "openai",
    "api_key": MOCK_API_KEY,
    "model": "gpt-5-test",
    "temperature": "0.5",
    "max_tokens": "500",
    "timeout": "60",
    "organization": "test_org",
}


def test_init_wrong_provider():
    """Test provider initialization fails with wrong provider."""
    config = MOCK_CONFIG.copy()
    config["provider"] = "anthropic"
    with pytest.raises(ValueError, match="Provider must be 'openai'"):
        OpenAIProvider(config)

def test_init_missing_provider():
    """Test provider initialization fails without provider field."""
    config = MOCK_CONFIG.copy()
    del config["provider"]
    with pytest.raises(ValueError, match="Provider must be 'openai'"):
        OpenAIProvider(config)

def test_init_minimal_config():
    """Test provider initialization with minimal config."""
    provider = OpenAIProvider(MOCK_CONFIG)
    assert provider.api_key == MOCK_API_KEY
    assert provider.model == DEFAULT_MODEL == "gpt-6-astra"
    assert provider.reasoning_effort == "low"
    assert provider.temperature == 0.0
    assert provider.max_tokens == 4096
    assert provider.timeout == 120.0

def test_init_dated_astra_defaults_to_low_effort():
    """Every gpt-6 model ID gets the low effort default, not only the bare name."""
    config = dict(MOCK_CONFIG, model="gpt-6-astra-2026-09-01")
    assert OpenAIProvider(config).reasoning_effort == "low"

def test_init_full_config():
    """Test provider initialization with full config."""
    provider = OpenAIProvider(MOCK_CONFIG_FULL)
    assert provider.api_key == MOCK_API_KEY
    assert provider.model == "gpt-5-test"
    assert provider.temperature == 0.5
    assert provider.max_tokens == 500
    assert provider.timeout == 60.0
    assert provider.organization == "test_org"


@pytest.mark.parametrize('config,effort', [
    ({'model': 'gpt-5'}, 'minimal'),
    ({'model': 'gpt-4o'}, None),
    ({'reasoning_effort': 'medium'}, 'medium'),
    ({'reasoning_effort': ''}, ''),
])
def test_preserves_model_and_effort_overrides(config, effort):
    provider = OpenAIProvider(dict(MOCK_CONFIG, **config))
    assert provider.model == config.get('model', 'gpt-6-astra')
    assert provider.reasoning_effort == effort

def test_init_missing_api_key():
    """Test provider initialization fails without API key."""
    config = {"provider": "openai"}
    with pytest.raises(KeyError):
        OpenAIProvider(config)

def test_get_config_schema():
    """Test config schema is valid and complete."""
    provider = OpenAIProvider(MOCK_CONFIG)
    schema = provider.get_config_schema()

    assert isinstance(schema, dict)
    assert "provider" in schema["properties"]
    assert "api_key" in schema["properties"]
    assert schema["required"] == ["provider", "api_key"]
    assert schema["properties"]["provider"]["enum"] == ["openai"]
    
    # Check optional fields are present
    assert "organization" in schema["properties"]
    assert "timeout" in schema["properties"]

@patch('openai.OpenAI')
def test_generate_command(mock_openai):
    """Test command generation with mocked OpenAI client."""
    # Setup mock response
    mock_choice = Mock()
    mock_choice.message.content = "ls -l\n##DANGERLEVEL=0## Safe command"
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    # Create provider and generate command
    provider = OpenAIProvider(MOCK_CONFIG)
    result = provider.generate_command(
        description="list files",
        context={"shell": "bash"},
        system_prompt="You are a CLI assistant"
    )

    # Verify result
    assert "ls -l" in result
    assert "##DANGERLEVEL=0##" in result

    # Verify OpenAI client was called correctly
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == DEFAULT_MODEL
    assert call_kwargs["reasoning_effort"] == "low"
    assert len(call_kwargs["messages"]) == 2
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][0]["content"] == "You are a CLI assistant"
    assert "list files" in call_kwargs["messages"][1]["content"]

@patch('openai.OpenAI')
def test_generate_command_api_error(mock_openai):
    """Test error handling when API call fails."""
    # Setup mock to raise exception
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = openai.APIError(
        message="API Error",
        request=Mock(),
        body={"error": {"message": "API Error", "type": "invalid_request_error"}}
    )
    mock_openai.return_value = mock_client

    provider = OpenAIProvider(MOCK_CONFIG)
    with pytest.raises(RuntimeError, match="OpenAI API error"):
        provider.generate_command(
            description="list files",
            context={"shell": "bash"},
            system_prompt="You are a CLI assistant"
        )

@patch('openai.OpenAI')
def test_generate_command_generic_error(mock_openai):
    """Test error handling for generic exceptions."""
    # Setup mock to raise generic exception
    mock_client = Mock()
    mock_client.chat.completions.create.side_effect = Exception("Generic error")
    mock_openai.return_value = mock_client

    provider = OpenAIProvider(MOCK_CONFIG)
    with pytest.raises(RuntimeError, match="Unexpected error"):
        provider.generate_command(
            description="list files",
            context={"shell": "bash"},
            system_prompt="You are a CLI assistant"
        )

def test_invalid_temperature():
    """Test provider initialization fails with invalid temperature."""
    config = MOCK_CONFIG.copy()
    config["temperature"] = "invalid"
    with pytest.raises(ValueError):
        OpenAIProvider(config)

def test_invalid_max_tokens():
    """Test provider initialization fails with invalid max_tokens."""
    config = MOCK_CONFIG.copy()
    config["max_tokens"] = "invalid"
    with pytest.raises(ValueError):
        OpenAIProvider(config)

def test_invalid_timeout():
    """Test provider initialization fails with invalid timeout."""
    config = MOCK_CONFIG.copy()
    config["timeout"] = "invalid"
    with pytest.raises(ValueError):
        OpenAIProvider(config)
