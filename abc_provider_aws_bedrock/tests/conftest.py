"""Test configuration and fixtures for abc-provider-aws-bedrock."""

import json
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_bedrock_client():
    """Fixture providing a mocked Bedrock client."""
    with patch('boto3.Session') as mock_session:
        # Setup mock response for converse
        mock_response = {
            'output': {
                'message': {
                    'role': 'assistant',
                    'content': [{'text': "echo test\n##DANGERLEVEL=0## Safe command"}]
                }
            },
            'usage': {
                'inputTokens': 50,
                'outputTokens': 20,
                'totalTokens': 70
            },
            'stopReason': 'end_turn'
        }
        mock_client = Mock()
        mock_client.converse.return_value = mock_response
        mock_session.return_value.client.return_value = mock_client
        yield mock_session

@pytest.fixture
def mock_config():
    """Fixture providing a basic valid configuration."""
    return {
        "provider": "aws-bedrock",
        "profile": "abc-cli",
    }

@pytest.fixture
def mock_config_full():
    """Fixture providing a full configuration with all options."""
    return {
        "provider": "aws-bedrock",
        "profile": "abc-cli",
        "model": "anthropic.claude-sonnet-4-20250514-v1:0",
        "region": "us-east-1",
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
