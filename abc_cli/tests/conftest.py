"""Test configuration and fixtures for abc-cli tests."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from pathlib import Path

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / ".config" / "abc"
    config_dir.mkdir(parents=True)
    return config_dir

@pytest.fixture
def mock_config_file(temp_config_dir):
    """Create a mock configuration file."""
    config_path = temp_config_dir / "config"
    config_content = """[default]
provider = mock_provider
api_key = test_key

[test_section]
provider = mock_provider
api_key = another_test_key
model = test-model
"""
    config_path.write_text(config_content)
    return str(config_path)

@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    provider.get_config_schema.return_value = {
        'required': ['provider', 'api_key'],
        'properties': {
            'provider': {'enum': ['mock_provider']},
            'api_key': {'type': 'string'},
            'model': {'type': 'string'}
        }
    }
    provider.generate_command.return_value = "ls -la\n##DANGERLEVEL=0## Safe command"
    return provider

@pytest.fixture
def mock_provider_entry_point(mock_provider):
    """Mock the provider entry point discovery."""
    entry_point = Mock()
    entry_point.name = 'mock_provider'
    entry_point.load.return_value = lambda config: mock_provider
    return entry_point

@pytest.fixture
def isolated_environment(monkeypatch, temp_config_dir):
    """Create an isolated environment for testing."""
    # Clear environment variables that might interfere
    monkeypatch.delenv('ABC_CONFIG', raising=False)
    monkeypatch.delenv('XDG_CONFIG_HOME', raising=False)
    
    # Set XDG_CONFIG_HOME to our temp directory
    monkeypatch.setenv('XDG_CONFIG_HOME', str(temp_config_dir.parent))
    
    # Clear any existing HOME-based configs
    monkeypatch.setenv('HOME', str(temp_config_dir.parent.parent))
    
    return temp_config_dir