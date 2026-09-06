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


@pytest.mark.parametrize('suffix', ['; t=$(mktemp); rm -f "$t"',
                                   '; printf data >/tmp/wordcounts; rm /tmp/wordcounts'])
def test_temporary_writes_are_not_read_only(suffix):
    result = evaluate(reference() + suffix)
    assert result['counting']['pass']
    assert not result['read_only']['pass']


def test_incorrect_answer_cannot_pass_by_mentioning_expected_word():
    result = evaluate('printf "alder cedar\\n"')
    assert not result['counting']['pass']


def test_incorrect_percentage():
    result = evaluate('printf "cedar (99%%)\\n"')
    assert not result['counting']['pass']


def test_answer_can_include_explanatory_text():
    result = evaluate('printf "The word is cedar, appearing in 2/4 files.\\n"')
    assert result['counting']['pass']


def test_silent_failure_has_reason():
    result = evaluate('exit 1')
    assert not result['empty']['pass']
    assert result['empty']['reason'] == 'Command exited with status 1'


def test_sparse_and_empty_file_regressions():
    command = reference().replace('0<c<n', '0<c<n and .4<=c/n<=.6')
    result = evaluate(command)
    assert result['counting']['pass']
    assert not result['sparse']['pass']
    command = reference().replace('if n]', 'if n and (root/os.fsdecode(n)).stat().st_size]')
    result = evaluate(command)
    assert result['counting']['pass']
    assert not result['empty_file']['pass']
