"""New installations write an OpenAI default and config sections must name a provider.

[Created with AI: Codex with GPT-6 Astra, Claude Code with Fable 5.1]
"""
import configparser
from pathlib import Path
from unittest.mock import patch
import pytest
from abc_cli import abc_generate, abc_setup


def test_runtime_rejects_config_without_provider():
    with pytest.raises(ValueError, match="no 'provider' setting"):
        abc_generate.get_provider({'api_key': 'test-key'})


def test_setup_substitutes_key_only_in_default_section(tmp_path):
    destination = tmp_path / 'config'
    with patch.object(abc_setup, 'get_config_paths', return_value=(destination, tmp_path / 'legacy')), \
            patch.object(abc_setup, 'show_instructions_and_confirm', return_value=True), \
            patch.object(abc_setup, 'get_terminal_input', return_value='test-openai-key'):
        assert abc_setup.setup_config(package_dir=Path(abc_setup.__file__).parent)
    assert destination.read_text().count('test-openai-key') == 1


def test_setup_writes_openai_key_and_astra_low(tmp_path):
    destination = tmp_path / 'config'
    with patch.object(abc_setup, 'get_config_paths', return_value=(destination, tmp_path / 'legacy')), \
            patch.object(abc_setup, 'show_instructions_and_confirm', return_value=True), \
            patch.object(abc_setup, 'get_terminal_input', return_value='test-openai-key'):
        assert abc_setup.setup_config(package_dir=Path(abc_setup.__file__).parent)
    config = configparser.ConfigParser()
    config.read(destination)
    assert dict(config['default']) == {'provider': 'openai', 'api_key': 'test-openai-key',
                                       'model': 'gpt-6-astra', 'reasoning_effort': 'low'}
