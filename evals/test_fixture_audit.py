"""Filesystem auditing includes transient writes outside the repository.

[Created with AI: Codex with GPT-6 Astra]
"""
import pytest
from evals.fixtures.markdown_word import writes_files


@pytest.mark.parametrize('trace', [
    '42 openat(AT_FDCWD, "/tmp/words", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 3',
    '42 unlink("/tmp/words") = 0',
    '42 mkdir("changed", 0777) = 0',
    '42 openat(AT_FDCWD, "changed", O_RDWR|O_CREAT, 0600 <unfinished ...>',
])
def test_detects_write_attempts(trace):
    assert writes_files(trace)


def test_reading_and_discarding_output_are_allowed():
    assert not writes_files('42 openat(AT_FDCWD, "doc.md", O_RDONLY) = 3\n'
                            '42 openat(AT_FDCWD, "/dev/null", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 2')


def test_bash_terminal_probe_and_command_arguments_are_not_writes():
    assert not writes_files('42 openat(AT_FDCWD, "/dev/tty", O_RDWR|O_NONBLOCK) = -1 ENXIO (No such device or address)\n'
                            '42 execve("/bin/bash", ["bash", "-c", "echo unlink(foo)"], []) = 0')


def test_failed_bytecode_cache_write_did_not_modify_files():
    assert not writes_files('42 openat(AT_FDCWD, "/usr/local/lib/python3.12/__pycache__/re.pyc", '
                            'O_WRONLY|O_CREAT|O_EXCL, 0644) = -1 EROFS (Read-only file system)')
