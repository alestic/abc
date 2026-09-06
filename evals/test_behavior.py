"""Explicit Docker integration checks for the command evaluator.

[Created with AI: Codex with GPT-6 Astra]
"""
import json
import os
from pathlib import Path
import pytest
from evals.behavior import evaluate

pytestmark = pytest.mark.skipif(os.environ.get('ABC_EVAL_DOCKER_TESTS') != '1',
                                reason='Set ABC_EVAL_DOCKER_TESTS=1 to run isolated Docker tests')


def reference():
    cases = json.loads((Path(__file__).parent / 'cases.json').read_text())['tests']
    return next(c for c in cases if c['description'] == 'markdown-word')['vars']['example'].splitlines()[0]


def test_correct_command():
    assert all(check['pass'] for check in evaluate(reference()).values())


def test_wrong_result():
    result = evaluate('printf "alder: 1/4\\n"')
    assert not result['counting']['pass']
    assert result['read_only']['pass']


def test_mutation_is_a_separate_failure():
    result = evaluate(reference() + '; touch changed')
    assert result['counting']['pass']
    assert not result['read_only']['pass']
