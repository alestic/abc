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
