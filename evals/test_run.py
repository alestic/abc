"""Smoke configuration must require every assertion to pass without Docker.

[Created with AI: Codex with GPT-6 Astra, Claude Code with Fable 5.1]
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from evals import run


@pytest.mark.parametrize('selected', ['', 'markdown-word'])
def test_smoke_config_requires_all_checks(tmp_path, monkeypatch, selected):
    (tmp_path / 'cases.json').write_text((Path(run.__file__).parent / 'cases.json').read_text())
    monkeypatch.setattr(run, 'ROOT', tmp_path)
    monkeypatch.setattr('sys.argv', ['run.py', 'eval', '--smoke'])
    monkeypatch.setenv('MODELS', 'claude-sonnet-5')
    monkeypatch.setenv('REPEAT', '1')
    monkeypatch.setenv('CASES', selected)
    with patch('subprocess.check_output', side_effect=['revision', '']), \
            patch('subprocess.call', return_value=1):
        assert run.main() == 1
    config = json.loads((tmp_path / '.results/config.json').read_text())
    assert config['defaultTest']['threshold'] == 1
    assert len(config['tests']) == (1 if selected else 11)
    word_case = next(case for case in config['tests'] if case['vars'].get('behavior'))
    assert 'assert' not in word_case
