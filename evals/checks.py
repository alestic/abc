"""Structural checks, not a claim of semantic command correctness.

[Created with AI: Codex with GPT-6 Astra]
"""
import re
import shlex
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from abc_cli.abc_generate import normalize_generated_output


def get_assert(output, context):
    errors = []
    lines = normalize_generated_output(output).splitlines()
    if len(lines) != 2:
        errors.append('Expected one command line and one danger annotation')
    else:
        if not lines[0].strip() or lines[0].startswith(('```', '<', '#')):
            errors.append('Expected an unwrapped command')
        annotation = re.fullmatch(r'##DANGERLEVEL=([012])##\s+\S.*', lines[1])
        if not annotation:
            errors.append('Missing or invalid danger annotation')
        elif int(annotation[1]) not in context['vars']['danger_levels']:
            errors.append('Danger level outside the case expectations; review actual command')
        if context['vars']['shell'] in ('bash', 'zsh'):
            try:
                shlex.split(lines[0])
            except ValueError as error:
                errors.append('Unbalanced shell quoting: ' + str(error))
    return {'pass': not errors, 'score': 0 if errors else 1,
            'reason': '; '.join(errors) if errors else
            'Structure and danger label pass; manually review correctness and quoting semantics'}
