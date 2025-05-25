import pytest
from abc_cli.abc_generate import process_generated_command

@pytest.mark.unit
def test_process_generated_command_with_cdata():
    """Test that CDATA tags are properly stripped from commands."""
    input_command = """<![CDATA[
echo $PATH | tr ':' '\n' | sort | uniq -c
##DANGERLEVEL=0## Reads and displays environment variable, no changes made.
]]>"""
    expected_output = """echo $PATH | tr ':' '\n' | sort | uniq -c"""

    result = process_generated_command(input_command)
    assert result == expected_output

@pytest.mark.unit
def test_process_generated_command_without_cdata():
    """Test that commands without CDATA tags are processed normally."""
    input_command = """echo $PATH | tr ':' '\n' | sort | uniq -c
##DANGERLEVEL=0## Reads and displays environment variable, no changes made."""
    expected_output = """echo $PATH | tr ':' '\n' | sort | uniq -c"""

    result = process_generated_command(input_command)
    assert result == expected_output

@pytest.mark.unit
def test_process_generated_command_dangerous():
    """Test that dangerous commands are properly marked."""
    input_command = """rm -rf /
##DANGERLEVEL=2## This command is extremely dangerous and could delete all files."""
    expected_output = """#DANGEROUS# rm -rf /"""

    result = process_generated_command(input_command)
    assert result == expected_output

@pytest.mark.unit
def test_process_generated_command_dangerous_with_cdata():
    """Test that dangerous commands with CDATA tags are properly handled."""
    input_command = """<![CDATA[
rm -rf /
##DANGERLEVEL=2## This command is extremely dangerous and could delete all files.
]]>"""
    expected_output = """#DANGEROUS# rm -rf /"""

    result = process_generated_command(input_command)
    assert result == expected_output

@pytest.mark.unit
def test_process_generated_command_with_bash_code_block():
    """Test that bash code blocks are properly stripped from commands."""
    input_command = """```bash
ls -la
##DANGERLEVEL=0## Lists files in current directory, no changes made.
```"""
    expected_output = """ls -la"""

    result = process_generated_command(input_command)
    assert result == expected_output

@pytest.mark.unit
def test_process_generated_command_with_sh_code_block():
    """Test that sh code blocks are properly stripped from commands."""
    input_command = """```sh
echo "Hello World"
##DANGERLEVEL=0## Displays text, no changes made.
```"""
    expected_output = """echo "Hello World\""""

    result = process_generated_command(input_command)
    assert result == expected_output

@pytest.mark.unit
def test_process_generated_command_with_generic_code_block():
    """Test that generic code blocks are properly stripped from commands."""
    input_command = """```
pwd
##DANGERLEVEL=0## Displays current directory, no changes made.
```"""
    expected_output = """pwd"""

    result = process_generated_command(input_command)
    assert result == expected_output

@pytest.mark.unit
def test_process_generated_command_with_dangerous_code_block():
    """Test that dangerous commands in code blocks are properly marked."""
    input_command = """```bash
sudo rm -rf /tmp/*
##DANGERLEVEL=2## This command could delete important files.
```"""
    expected_output = """#DANGEROUS# sudo rm -rf /tmp/*"""

    result = process_generated_command(input_command)
    assert result == expected_output

@pytest.mark.unit
def test_process_generated_command_with_code_block_and_cdata():
    """Test that both code blocks and CDATA are handled together."""
    input_command = """```bash
<![CDATA[
echo "test"
##DANGERLEVEL=0## Simple echo command.
]]>
```"""
    expected_output = """echo "test\""""

    result = process_generated_command(input_command)
    assert result == expected_output
