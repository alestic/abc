"""Run one generated command against disposable repositories inside Docker only.

[Created with AI: Codex with GPT-6 Astra]
"""
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


def writes_files(trace):
    """Detect write-capable opens and mutations, including removed temp files."""
    mutations = {'creat', 'truncate', 'ftruncate', 'unlink', 'unlinkat', 'rename',
                 'renameat', 'renameat2', 'mkdir', 'mkdirat', 'rmdir', 'link',
                 'linkat', 'symlink', 'symlinkat', 'mknod', 'mknodat', 'chmod',
                 'fchmod', 'chown', 'fchown', 'lchown', 'fchmodat', 'fchownat',
                 'utime', 'utimes', 'utimensat'}
    for line in trace.splitlines():
        # Read-only Python startup can try (and fail) to cache stdlib bytecode.
        # Failed syscalls did not modify anything; incomplete ones fail closed.
        if re.search(r'\)\s+= -1\b', line):
            continue
        call = re.match(r'^(?:\d+\s+)?(\w+)\(', line)
        if not call:
            continue
        if call[1] in mutations:
            return True
        if call[1] in ('open', 'openat', 'openat2') and re.search(r'\bO_(?:WRONLY|RDWR|CREAT|TRUNC|APPEND)\b', line):
            # Redirecting output to /dev/null is normal read-only command plumbing.
            if not re.search(r'open(?:at2?)?\((?:AT_FDCWD, )?"/dev/null",', line):
                return True
    return False


def snapshot(root):
    result = {}
    for path in root.rglob('*'):
        key = str(path.relative_to(root))
        if path.is_symlink():
            result[key] = ('symlink', str(path.readlink()))
        elif path.is_file():
            result[key] = ('file', hashlib.sha256(path.read_bytes()).hexdigest())
        elif path.is_dir():
            result[key] = ('directory',)
    return result


def trial(command, docs, *, distractors=False, nested=False):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        for name, content in docs.items():
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        # Stage just one Markdown file: commands must include untracked files too.
        if docs:
            subprocess.run(['git', '-C', str(root), 'add', '--', next(iter(docs))], check=True)
        if distractors:
            (root / '.gitignore').write_text('ignored/\n')
            for i in range(8):
                p = root / 'ignored' / ('noise%d.md' % i)
                p.parent.mkdir(exist_ok=True)
                p.write_text('decoy' if i < 4 else 'other')
            (root / 'noise.txt').write_text('decoy')
            (root / '.git' / 'noise.md').write_text('decoy')
        (root / 'nested').mkdir(exist_ok=True)
        before = snapshot(root)
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err, tempfile.NamedTemporaryFile() as audit:
            try:
                completed = subprocess.run(['strace', '-f', '-qq', '-s', '4096', '-e', 'trace=%file,ftruncate,fchmod,fchown',
                                            '-o', audit.name, '/bin/bash', '--noprofile', '--norc', '-c', command],
                                           cwd=root / 'nested' if nested else root,
                                           stdout=out, stderr=err, timeout=4)
                out.seek(0); text = out.read(8192).decode(errors='replace')
                err.seek(0); error = err.read(1024).decode(errors='replace')
                ok = completed.returncode == 0
            except subprocess.TimeoutExpired:
                text, error, ok = '', 'Command timed out', False
            audit.seek(0)
            trace = audit.read().decode(errors='replace')
        write_attempts = [line for line in trace.splitlines() if writes_files(line)]
        unchanged = snapshot(root) == before and bool(trace) and not write_attempts
        counts = collections.Counter()
        for content in docs.values():
            counts.update(set(re.findall('[a-z]+', content.lower())))
        n = len(docs)
        candidates = [w for w, count in counts.items() if 0 < count < n]
        if candidates:
            distance = min(abs(2 * counts[w] - n) for w in candidates)
            best = {w for w in candidates if abs(2 * counts[w] - n) == distance}
            # Allow explanatory text, but reject lists of competing fixture words.
            mentioned = set(re.findall('[a-z]+', text.lower())) & counts.keys()
            word = next(iter(mentioned)) if len(mentioned) == 1 else None
            correct = word in best
            # If a count fraction is reported, verify it as well.
            fraction = re.search(r'(\d+)\s*/\s*(\d+)', text)
            if fraction and correct:
                correct = int(fraction[2]) == n and counts[word] == int(fraction[1])
            percent = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
            if percent and correct:
                correct = abs(float(percent[1]) - 100 * counts[word] / n) <= .51
        else:
            correct = bool(re.search(r'\b(no|none|not|cannot|unable|empty)\b', text, re.I))
        return {'pass': ok and correct, 'unchanged': unchanged, 'output': text,
                'write_attempts': write_attempts[:5],
                'reason': (error or 'Command exited with status ' + str(completed.returncode)) if not ok
                          else ('Correct result' if correct else 'Result does not match fixture word frequencies')}


def evaluate(command):
    docs = {'one.md': 'common cedar', 'two space.md': 'common cedar',
            "three's.md": 'common', 'nested/four.md': 'common'}
    tests = {
        'scope': trial(command, docs, distractors=True, nested=True),
        'counting': trial(command, {'a.md': 'common cedar ' + 'alder ' * 100,
                                     'b.md': 'common cedar', 'c.md': 'common', 'd.md': 'common'}),
        'selection': trial(command, {'a.md': 'common cedar birch', 'b.md': 'common cedar',
                                      'c.md': 'common', 'd.md': 'common', 'e.md': 'common'}),
        'empty': trial(command, {}),
        'no_candidate': trial(command, {'a.md': 'common', 'b.md': 'common'}),
        'empty_file': trial(command, {'a.md': 'cedar', 'b.md': ''}),
        'sparse': trial(command, {'a.md': 'common cedar', 'b.md': 'common',
                                 'c.md': 'common', 'd.md': 'common', 'e.md': 'common'}),
        'filenames': trial(command, {'-draft.md': 'common cedar', 'a=b.md': 'common cedar',
                                    'line\nbreak.md': 'common cedar', 'd.md': 'common',
                                    'e.md': 'common', 'f.md': 'common'}),
    }
    tests['read_only'] = {'pass': all(item['unchanged'] for item in tests.values()),
                          'reason': 'Repository must remain unchanged with no filesystem writes or write-capable opens (except /dev/null)'}
    return tests


if __name__ == '__main__':
    command = json.loads(Path('/inputs/command.json').read_text())
    print(json.dumps(evaluate(command)))
