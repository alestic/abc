"""Smoke configuration must require every binary assertion to pass.

[Created with AI: Codex with GPT-6 Astra]
"""
import json
from pathlib import Path
from unittest.mock import patch
from evals import run


def test_smoke_config_requires_all_checks(tmp_path, monkeypatch):
    (tmp_path / 'cases.json').write_text((Path(run.__file__).parent / 'cases.json').read_text())
    monkeypatch.setattr(run, 'ROOT', tmp_path)
    monkeypatch.setattr('sys.argv', ['run.py', 'eval', '--smoke'])
    monkeypatch.setenv('MODELS', 'claude-sonnet-5')
    monkeypatch.setenv('REPEAT', '1')
    monkeypatch.setenv('CASES', 'markdown-word')
    with patch('evals.behavior.check_available'), \
            patch('subprocess.check_output', side_effect=['revision', '']), \
            patch('subprocess.call', return_value=1):
        assert run.main() == 1
    config = json.loads((tmp_path / '.results/config.json').read_text())
    assert config['defaultTest']['threshold'] == 1
    checks = {item['config']['check'] for item in config['tests'][0]['assert']}
    assert {'empty_file', 'sparse', 'filenames', 'read_only'} <= checks
