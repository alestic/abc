"""Run one generated command against disposable repositories inside Docker only.

[Created with AI: Codex with GPT-6 Astra, Claude Code with Fable 5.1]
"""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

CHECKS = ('word', 'no_candidate')
WORD = re.compile('[a-z]+')
FRACTION = re.compile(r'\d+\s*/\s*\d+')


def snapshot(root):
    """Map every path under root, including ignored files and .git, to its content hash."""
    state = {}
    for path in root.rglob('*'):
        key = str(path.relative_to(root))
        if path.is_symlink():
            state[key] = 'link:' + os.readlink(path)
        elif path.is_file():
            state[key] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            state[key] = 'dir'
    return state


def trial(command, docs):
    """Run the command from a subdirectory of a fresh repository holding docs.

    One Markdown file is tracked and the rest are untracked, so commands must
    include untracked files. Ignored and non-Markdown decoys contain a word that
    would win if they were counted.
    """
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        for name, content in docs.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(content)
        if docs:
            subprocess.run(['git', '-C', str(root), 'add', '--', next(iter(docs))], check=True)
        (root / '.gitignore').write_text('ignored/\n')
        (root / 'ignored').mkdir()
        (root / 'ignored' / 'one.md').write_text('alder')
        (root / 'ignored' / 'two.md').write_text('alder')
        (root / 'noise.txt').write_text('alder')
        (root / 'nested').mkdir(exist_ok=True)
        before = snapshot(root)
        try:
            completed = subprocess.run(['/bin/bash', '--noprofile', '--norc', '-c', command],
                                       cwd=root / 'nested', capture_output=True, text=True, timeout=4)
        except subprocess.TimeoutExpired:
            return {'pass': False, 'reason': 'Command timed out', 'output': ''}
        output = completed.stdout
        if completed.returncode:
            reason = completed.stderr.strip() or 'Command exited with status ' + str(completed.returncode)
            return {'pass': False, 'reason': reason, 'output': output}
        if snapshot(root) != before:
            return {'pass': False, 'reason': 'Command modified the repository', 'output': output}
        counts = collections.Counter()
        for content in docs.values():
            counts.update(set(WORD.findall(content.lower())))
        n = len(docs)
        candidates = [w for w, count in counts.items() if 0 < count < n]
        mentioned = set(WORD.findall(output.lower())) & counts.keys()
        if candidates:
            distance = min(abs(2 * counts[w] - n) for w in candidates)
            best = {w for w in candidates if abs(2 * counts[w] - n) == distance}
            correct = len(mentioned) == 1 and mentioned <= best
        else:
            correct = not mentioned and not FRACTION.search(output)
        return {'pass': correct, 'output': output,
                'reason': 'Correct result' if correct else 'Result does not match fixture word frequencies'}


def evaluate(command):
    # cedar is in 2 of 4 files but appears 4 times, so counting occurrences
    # instead of files excludes it and picks birch (3 of 4). Counting the alder
    # decoys makes alder the answer.
    return {
        'word': trial(command, {'one.md': 'spruce cedar cedar birch',
                                'two space.md': 'spruce cedar cedar birch',
                                'three.md': 'spruce birch', 'nested/four.md': 'spruce'}),
        'no_candidate': trial(command, {'a.md': 'spruce', 'b.md': 'spruce'}),
    }


if __name__ == '__main__':
    print(json.dumps(evaluate(json.loads(Path('/inputs/command.json').read_text()))))
