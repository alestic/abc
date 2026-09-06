"""Isolated behavioral evaluations of generated commands.

[Created with AI: Codex with GPT-6 Astra]
"""
import json
from pathlib import Path
import subprocess
import tempfile
import uuid

IMAGE = 'abc-eval-fixtures:1'


def check_available():
    try:
        subprocess.run(['docker', 'image', 'inspect', IMAGE], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError('Markdown-word eval requires Docker and `make eval-image`') from error


def evaluate(command):
    name = 'abc-eval-' + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='abc-eval-') as directory:
        path = Path(directory)
        path.chmod(0o755)
        (path / 'command.json').write_text(json.dumps(command))
        (path / 'runner.py').write_text((Path(__file__).parent / 'fixtures' / 'markdown_word.py').read_text())
        args = ['docker', 'run', '--rm', '--name', name, '--network=none', '--read-only',
                '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=65534:65534',
                '--pids-limit=64', '--memory=256m', '--cpus=1',
                '--tmpfs=/tmp:rw,nosuid,nodev,size=64m,mode=1777',
                '--mount', 'type=bind,src=' + str(path) + ',dst=/inputs,readonly',
                IMAGE, 'python3', '/inputs/runner.py']
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=35)
            if result.returncode:
                return {'error': 'Fixture container failed: ' + result.stderr[-1000:]}
            return json.loads(result.stdout)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            return {'error': 'Fixture execution failed: ' + str(error)}
        finally:
            # Also remove a container if the client timed out or was interrupted.
            try:
                subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=10)
            except (OSError, subprocess.SubprocessError):
                pass
