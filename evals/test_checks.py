"""Regression checks for the offline evaluation grader.

[Created with AI: Codex with GPT-6 Astra]
"""
import pytest
from evals.checks import get_assert


@pytest.mark.parametrize('output', [
    'ls',
    'ls\n##DANGERLEVEL=2## Destructive',
    "cat 'broken\n##DANGERLEVEL=0## Read only",
    '```bash\nls\n```',
    'ls\n##DANGERLEVEL=0##',
])
def test_rejects_invalid_output(output):
    assert not get_assert(output, {'vars': {'shell': 'bash', 'danger_levels': [0]}})['pass']


def test_accepts_literal_quoted_filename():
    output = "cat -- '*.txt'\n##DANGERLEVEL=0## Read only"
    assert get_assert(output, {'vars': {'shell': 'bash', 'danger_levels': [0]}})['pass']

@pytest.mark.parametrize('output', [
    '```\nls -la\n```\n##DANGERLEVEL=0## Read only',
    '```bash\nls -la\n##DANGERLEVEL=0## Read only\n```',
    '<![CDATA[\nls -la\n##DANGERLEVEL=0## Read only\n]]>',
])
def test_accepts_application_supported_wrappers(output):
    from abc_cli.abc_generate import process_generated_command
    assert get_assert(output, {'vars': {'shell': 'bash', 'danger_levels': [0]}})['pass']
    assert process_generated_command(output) == 'ls -la'


def test_independent_checks():
    from evals.checks import format_check, danger_check, quoting_check
    output = '```bash\ncp -n a b\n```\n##DANGERLEVEL=0## Read only'
    context = {'vars': {'shell': 'bash', 'danger_levels': [1]}}
    assert format_check(output, context)['pass']
    assert quoting_check(output, context)['pass']
    assert not danger_check(output, context)['pass']


def test_bash_ansi_c_quoting():
    output = "printf '%s' $'O\\'Brien'\n##DANGERLEVEL=0## Read only"
    assert get_assert(output, {'vars': {'shell': 'bash', 'danger_levels': [0]}})['pass']


def test_balanced_quotes_do_not_imply_valid_shell_syntax():
    output = '(printf hello))\n##DANGERLEVEL=0## Read only'
    assert not get_assert(output, {'vars': {'shell': 'bash', 'danger_levels': [0]}})['pass']


def test_syntax_check_does_not_execute_commands_or_bash_env(tmp_path, monkeypatch):
    from evals.checks import quoting_check
    marker = tmp_path / 'executed'
    startup = tmp_path / 'startup'
    startup.write_text(f'touch {marker}\n')
    monkeypatch.setenv('BASH_ENV', str(startup))
    assert quoting_check(f'touch {marker}; echo $(touch {marker})\n##DANGERLEVEL=1## Write',
                         {'vars': {'shell': 'bash'}})['pass']
    assert not marker.exists()


def test_behavior_failure_always_has_reason():
    from evals.checks import behavior_check
    result = behavior_check('', {'config': {'check': 'empty'},
                                  'metadata': {'behavior': {'empty': {'pass': False, 'reason': ''}}}})
    assert result['pass'] is False
    assert result['score'] == 0
    assert result['reason']
