"""Saved aggregate flags must not hide failed assertions.

[Created with AI: Codex with GPT-6 Astra]
"""
import json
from evals.summary import print_summary


def test_summary_rejects_inconsistent_pass(tmp_path, capsys):
    rows = [{'provider': {'label': 'test-model'}, 'success': True,
             'gradingResult': {'componentResults': [{'pass': False, 'reason': ''}]}}]
    path = tmp_path / 'results.json'
    path.write_text(json.dumps({'results': {'results': rows}}))
    print_summary(path)
    assert '0/1' in capsys.readouterr().out
