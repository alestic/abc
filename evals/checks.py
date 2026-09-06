"""Structural checks, not a claim of semantic command correctness.

[Created with AI: Codex with GPT-6 Astra, Claude Code with Fable 5.1]
"""
import re
import shlex
import os
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from abc_cli.abc_generate import DANGER_LEVEL_PATTERN, normalize_generated_output


def result(passed, reason):
    # Promptfoo 0.122.2 derives aggregate pass/fail from the failure reason.
    return {'pass': passed, 'score': int(passed),
            'reason': reason or ('Check passed' if passed else 'Check failed')}


def split_output(output):
    """Return (command, danger annotation match) or None when the shape is wrong."""
    lines = normalize_generated_output(output).splitlines()
    if len(lines) != 2 or not lines[0].strip() or lines[0].startswith(('```', '#')):
        return None
    match = re.fullmatch(DANGER_LEVEL_PATTERN, lines[1])
    return (lines[0], match) if match else None


def format_check(output, context):
    valid = split_output(output) is not None
    return result(valid, 'Command and danger annotation present' if valid else
                  'Expected one command line and one valid danger annotation')


def danger_check(output, context):
    parts = split_output(output)
    valid = bool(parts and int(parts[1][1]) in context['vars']['danger_levels'])
    return result(valid, 'Danger label matches expectations' if valid else
                  'Danger level outside case expectations or missing')


def quoting_check(output, context):
    parts = split_output(output)
    if not parts:
        return result(False, 'No command')
    command = parts[0]
    if context['vars']['shell'] == 'bash':
        try:
            checked = subprocess.run(['/bin/bash', '--noprofile', '--norc', '-n'],
                                     input=command, capture_output=True, text=True, timeout=5,
                                     env={'PATH': os.defpath, 'LC_ALL': 'C'})
        except (OSError, subprocess.SubprocessError) as error:
            return result(False, 'Bash syntax check unavailable: ' + str(error))
        return result(checked.returncode == 0,
                      checked.stderr.strip() or 'Valid Bash syntax; command was not executed')
    if context['vars']['shell'] == 'zsh':
        try:
            shlex.split(command)
        except ValueError as error:
            return result(False, 'Unbalanced shell quoting: ' + str(error))
    return result(True, 'Balanced quoting; not a semantic correctness check')


def behavior_check(output, context):
    metadata = context.get('metadata') or context.get('providerResponse', {}).get('metadata', {})
    behavior = metadata.get('behavior', {})
    key = context['config']['check']
    check = behavior.get(key)
    if not check:
        return result(False, behavior.get('error', 'Behavioral result unavailable'))
    return result(bool(check['pass']), check['reason'])

