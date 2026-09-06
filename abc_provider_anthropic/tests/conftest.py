"""Test configuration and fixtures for abc-provider-anthropic."""

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_anthropic():
    """Fixture providing a mocked Anthropic client."""
    with patch('anthropic.Anthropic') as mock:
        # Setup default mock response
        mock_message = Mock()
        mock_message.content = [Mock(type='text', text="echo test\n##DANGERLEVEL=0## Safe command")]
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock.return_value = mock_client
        yield mock

@pytest.fixture
def mock_config():
    """Fixture providing a basic valid configuration."""
    return {
        "api_key": "test_api_key",
    }

@pytest.fixture
def mock_config_full():
    """Fixture providing a full configuration with all options."""
    return {
        "api_key": "test_api_key",
        "model": "claude-test",
        "temperature": "0.5",
        "max_tokens": "500",
    }

@pytest.fixture
def mock_context():
    """Fixture providing a basic context dictionary."""
    return {
        "shell": "bash",
        "os_info": "Ubuntu 22.04",
    }

# [Created with AI: Codex with GPT-6 Astra]
