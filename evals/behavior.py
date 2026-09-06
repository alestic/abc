"""Isolated behavioral evaluations of generated commands.

[Created with AI: Codex with GPT-6 Astra, Claude Code with Fable 5.1]
"""
import json
from pathlib import Path
import subprocess
import tempfile

from evals.fixtures.markdown_word import CHECKS  # noqa: F401  re-exported for run.py

IMAGE = 'abc-eval-fixtures'
RUNNER = Path(__file__).parent / 'fixtures' / 'markdown_word.py'


def docker_run(inputs, *command):
    return ['docker', 'run', '--rm', '--network=none', '--memory=256m', '--pids-limit=64',
            '--user=65534:65534', '--volume', str(inputs) + ':/inputs:ro', IMAGE, *command]


def check_available():
    """Run a trivial container with the evaluation flags before spending model calls."""
    with tempfile.TemporaryDirectory(prefix='abc-eval-') as directory:
        try:
            subprocess.run(docker_run(directory, 'true'), check=True, timeout=30,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError) as error:
            raise ValueError('Markdown-word eval requires Docker and `make eval-image`') from error


def evaluate(command):
    with tempfile.TemporaryDirectory(prefix='abc-eval-') as directory:
        path = Path(directory)
        path.chmod(0o755)
        for name, text in (('command.json', json.dumps(command)), ('runner.py', RUNNER.read_text())):
            (path / name).write_text(text)
            (path / name).chmod(0o644)
        try:
            result = subprocess.run(docker_run(path, 'python3', '/inputs/runner.py'),
                                    capture_output=True, text=True, timeout=30)
            if result.returncode:
                return {'error': 'Fixture container failed: ' + result.stderr[-1000:]}
            return json.loads(result.stdout)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            return {'error': 'Fixture execution failed: ' + str(error)}
