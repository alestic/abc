"""Tests for the Anthropic LLM provider."""

import pytest
from unittest.mock import Mock, patch
import anthropic

from abc_provider_anthropic.llm_provider import AnthropicProvider, DEFAULT_MODEL

# Test configuration
MOCK_API_KEY = "test_api_key"
MOCK_CONFIG = {
    "provider": "anthropic",
    "api_key": MOCK_API_KEY,
}

MOCK_CONFIG_FULL = {
    "provider": "anthropic",
    "api_key": MOCK_API_KEY,
    "model": "claude-test",
    "temperature": "0.5",
    "max_tokens": "500",
}

def test_init_wrong_provider():
    """Test provider initialization fails with wrong provider."""
    config = MOCK_CONFIG.copy()
    config["provider"] = "openai"
    with pytest.raises(ValueError, match="Provider must be 'anthropic'"):
        AnthropicProvider(config)

def test_init_missing_provider():
    """Test provider initialization fails without provider field."""
    config = MOCK_CONFIG.copy()
    del config["provider"]
    with pytest.raises(ValueError, match="Provider must be 'anthropic'"):
        AnthropicProvider(config)

def test_init_minimal_config():
    """Test provider initialization with minimal config."""
    provider = AnthropicProvider(MOCK_CONFIG)
    assert provider.api_key == MOCK_API_KEY
    assert provider.model == DEFAULT_MODEL
    assert provider.temperature is None
    assert provider.max_tokens == 1000

def test_init_full_config():
    """Test provider initialization with full config."""
    provider = AnthropicProvider(MOCK_CONFIG_FULL)
    assert provider.api_key == MOCK_API_KEY
    assert provider.model == "claude-test"
    assert provider.temperature == 0.5
    assert provider.max_tokens == 500

def test_init_missing_api_key():
    """Test provider initialization fails without API key."""
    with pytest.raises(KeyError):
        AnthropicProvider({"provider": "anthropic"})

def test_get_config_schema():
    """Test config schema is valid and complete."""
    provider = AnthropicProvider(MOCK_CONFIG)
    schema = provider.get_config_schema()

    assert isinstance(schema, dict)
    assert "provider" in schema["properties"]
    assert "api_key" in schema["properties"]
    assert schema["required"] == ["provider", "api_key"]
    assert schema["properties"]["provider"]["enum"] == ["anthropic"]

@patch('anthropic.Anthropic')
def test_generate_command(mock_anthropic):
    """Test command generation with mocked Anthropic client."""
    # Setup mock response
    mock_message = Mock()
    mock_message.content = [Mock(type='text', text="ls -l\n##DANGERLEVEL=0## Safe command")]
    mock_client = Mock()
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client

    # Create provider and generate command
    provider = AnthropicProvider(MOCK_CONFIG)
    result = provider.generate_command(
        description="list files",
        context={"shell": "bash"},
        system_prompt="You are a CLI assistant"
    )

    # Verify result
    assert "ls -l" in result
    assert "##DANGERLEVEL=0##" in result

    # Verify Anthropic client was called correctly
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == DEFAULT_MODEL
    assert call_kwargs["system"] == "You are a CLI assistant"
    assert len(call_kwargs["messages"]) == 1
    assert "list files" in call_kwargs["messages"][0]["content"][0]["text"]
    # Temperature must be omitted by default — newer Claude models reject it
    assert "temperature" not in call_kwargs

@patch('anthropic.Anthropic')
def test_generate_command_with_temperature(mock_anthropic):
    """Test temperature is sent only when explicitly configured."""
    mock_message = Mock()
    mock_message.content = [Mock(type='text', text="ls -l\n##DANGERLEVEL=0## Safe command")]
    mock_client = Mock()
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client

    provider = AnthropicProvider(MOCK_CONFIG_FULL)
    provider.generate_command(
        description="list files",
        context={"shell": "bash"},
        system_prompt="You are a CLI assistant"
    )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["temperature"] == 0.5

@patch('anthropic.Anthropic')
def test_generate_command_api_error(mock_anthropic):
    """Test error handling when API call fails."""
    # Setup mock to raise exception
    mock_client = Mock()
    mock_request = Mock()
    mock_request.method = "POST"
    mock_request.url = "https://api.anthropic.com/v1/messages"
    mock_client.messages.create.side_effect = anthropic.APIError(
        message="API Error",
        request=mock_request,
        body={"error": {"message": "API Error", "type": "invalid_request_error"}}
    )
    mock_anthropic.return_value = mock_client

    provider = AnthropicProvider(MOCK_CONFIG)
    with pytest.raises(anthropic.APIError):
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
        AnthropicProvider(config)

def test_invalid_max_tokens():
    """Test provider initialization fails with invalid max_tokens."""
    config = MOCK_CONFIG.copy()
    config["max_tokens"] = "invalid"
    with pytest.raises(ValueError):
        AnthropicProvider(config)

# [Created with AI: Codex with GPT-6 Astra]

@pytest.mark.parametrize('blocks, stop_reason, expected', [
    ([anthropic.types.ThinkingBlock(type='thinking', thinking='reasoning', signature='test'),
      anthropic.types.TextBlock(type='text', text='ls\n'),
      anthropic.types.TextBlock(type='text', text='##DANGERLEVEL=0## Read only')],
     'end_turn', 'ls\n##DANGERLEVEL=0## Read only'),
    ([anthropic.types.ThinkingBlock(type='thinking', thinking='reasoning', signature='test')],
     'end_turn', None),
    ([anthropic.types.TextBlock(type='text', text='rm -')], 'max_tokens', None),
])
@patch('anthropic.Anthropic')
def test_response_blocks(mock_client, blocks, stop_reason, expected):
    mock_client.return_value.messages.create.return_value = Mock(
        content=blocks, stop_reason=stop_reason)
    provider = AnthropicProvider(MOCK_CONFIG)
    if expected is None:
        with pytest.raises(ValueError):
            provider.generate_command('test', {}, 'system')
    else:
        assert provider.generate_command('test', {}, 'system') == expected
