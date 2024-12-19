#!/usr/bin/env python3
"""
abc_setup - Setup script for abc shell integration

This script manages shell integration scripts and configuration for abc.

Command line options:
  --uninstall   Remove shell integration scripts and optionally configuration
  --no-prompt   Skip all prompts and use default values (useful for automation)

Examples:
  # Normal installation with prompts
  abc_setup

  # Non-interactive installation with defaults
  abc_setup --no-prompt

  # Remove shell integration
  abc_setup --uninstall

  # Non-interactive uninstall (leaves configuration file in place)
  abc_setup --uninstall --no-prompt
"""

import argparse
import importlib.resources
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
import getpass

# Constants
SHELL_RC_FILES = {
    'bash': '.bashrc',
    'zsh': '.zshrc',
    'tcsh': '.tcshrc'
}

MARKER_BEGIN = "# >>> abc initialize >>>"
MARKER_MIDDLE = "# !! Contents within this block are managed by 'abc_setup' !!"
MARKER_END = "# <<< abc initialize <<<"

# Setup logging
logging.basicConfig(
    format='%(asctime)s [abc] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

def get_terminal_input(prompt='', default=None, sensitive=False):
    """Get user input from terminal, handling both interactive and non-interactive cases."""
    if not sys.stderr.isatty():
        return default

    print(prompt, end='', file=sys.stderr, flush=True)
    try:
        if sensitive:
            response = getpass.getpass(prompt='')
        else:
            with open('/dev/tty', 'r') as tty:
                response = tty.readline().strip()
    except (OSError, IOError):
        print(file=sys.stderr)
        return default

    print(file=sys.stderr)
    return response if response else default

def prompt_user(message, default=True, no_prompt=False):
    """Prompt user for yes/no confirmation."""
    if no_prompt:
        return default

    prompt = f"{message} [{'Y/n' if default else 'y/N'}] "
    response = get_terminal_input(prompt, 'y' if default else 'n')
    return response.lower() in ['y', 'yes']

def backup_file(file_path, timestamp):
    """Create a backup of a file with timestamp."""
    backup_path = file_path.with_suffix(f'.bak_{timestamp}')
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup: {backup_path}")

def find_abc_block(content):
    """Find and extract the abc block from file content.

    Returns:
        tuple: (block_content, start_index, end_index) or (None, -1, -1) if not found

    Raises:
        ValueError: If a corrupted block is found (begin marker without end marker)
    """
    existing_block = []
    in_block = False
    block_start_idx = -1
    block_end_idx = -1

    for i, line in enumerate(content):
        if MARKER_BEGIN in line:
            if in_block:
                # Found second begin marker before an end marker
                raise ValueError("Corrupted abc block: Found nested begin marker")
            in_block = True
            block_start_idx = i
        elif MARKER_END in line:
            if not in_block:
                raise ValueError("Corrupted abc block: Found end marker without begin marker")
            in_block = False
            block_end_idx = i
        elif in_block:
            existing_block.append(line)

    if block_start_idx != -1:
        if block_end_idx == -1:
            raise ValueError("Corrupted abc block: Missing end marker")
        return existing_block, block_start_idx, block_end_idx
    return None, -1, -1

def create_abc_block(source_line):
    """Create a new abc block with the given source line."""
    return [
        f"{MARKER_BEGIN}\n",
        f"{MARKER_MIDDLE}\n",
        f"{source_line}\n",
        f"{MARKER_END}\n"
    ]

def is_block_up_to_date(existing_block, source_line):
    """Check if the existing block content matches the expected content."""
    return existing_block == [f"{MARKER_MIDDLE}\n", f"{source_line}\n"]

def remove_abc_block(content):
    """Remove abc block from content if it exists.

    Returns:
        tuple: (new_content, found_block)
    """
    new_content = []
    in_block = False
    found_block = False

    for line in content:
        if MARKER_BEGIN in line:
            in_block = True
            found_block = True
        elif MARKER_END in line:
            in_block = False
        elif not in_block:
            new_content.append(line)

    return new_content, found_block

def check_needs_modification(content, source_line, remove=False):
    """Check if file needs modification without changing it.

    Returns:
        bool: True if file needs modification, False otherwise
    """
    try:
        if remove:
            # Check if block exists to remove
            for line in content:
                if MARKER_BEGIN in line:
                    return True
            return False
        else:
            # Check if block needs to be added/updated
            existing_block, _, _ = find_abc_block(content)
            if existing_block is None:
                return True  # Need to add new block
            return not is_block_up_to_date(existing_block, source_line)  # Need to update if not up to date
    except ValueError:
        return False  # Don't modify corrupted files

def read_rc_file(file_path):
    """Read lines from the rc file, return list of lines or None if not found."""
    path = Path.home() / file_path
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return f.readlines()

def write_rc_file(file_path, lines):
    """Write lines back to the rc file."""
    path = Path.home() / file_path
    with open(path, 'w') as f:
        f.writelines(lines)

def try_modify_rc_file(file_path, source_line, remove=False):
    """Check if modification is needed and perform it if required."""
    lines = read_rc_file(file_path)
    if lines is None:
        logging.info(f"Skipping {Path.home() / file_path}: file not found")
        return False

    if not check_needs_modification(lines, source_line, remove):
        logging.info(f"Skipping {Path.home() / file_path}: no modification needed")
        return False

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = (Path.home() / file_path).with_suffix(f'.bak_{timestamp}')
    shutil.copy2(Path.home() / file_path, backup_path)
    logging.info(f"Created backup: {backup_path}")

    if remove:
        new_lines, _ = remove_abc_block(lines)
        logging.info(f"Removing abc block from {Path.home() / file_path}")
    else:
        try:
            existing_block, start, end = find_abc_block(lines)
            new_block = create_abc_block(source_line)
            if existing_block is not None:
                # Update existing block
                lines[start:end+1] = new_block
                logging.info(f"Updating abc block in {Path.home() / file_path}")
            else:
                # Add new block
                if lines and lines[-1].strip():
                    lines.append('\n')  # Add newline if file doesn't end with one
                lines.extend(new_block)
                logging.info(f"Adding abc block to {Path.home() / file_path}")
            new_lines = lines
        except ValueError as e:
            logging.error(f"Error processing {Path.home() / file_path}: {str(e)}")
            return False

    write_rc_file(file_path, new_lines)
    return True

def setup_config(no_prompt=False):
    """Set up abc configuration file with API key."""
    config_file = Path.home() / '.abc.conf'

    # Check if we should configure
    if config_file.exists() and not prompt_user("\nConfiguration file already exists. Would you like to reconfigure it?", default=False, no_prompt=no_prompt):
        return True

    try:
        # Backup existing config if it exists
        if config_file.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file(config_file, timestamp)

        # Get the template content
        with importlib.resources.path('abc_cli', 'abc.conf.template') as template_path:
            with open(template_path, 'r') as f:
                template_content = f.read()

        # Prompt for API key if interactive
        print("\nPlease enter your Anthropic API key", file=sys.stderr)
        print("(You can get this from https://console.anthropic.com/settings/keys)", file=sys.stderr)
        api_key = get_terminal_input("API key: ", '{ANTHROPIC_API_KEY}', sensitive=True)

        # Write configuration
        config_content = template_content.replace('{ANTHROPIC_API_KEY}', api_key)
        with open(config_file, 'w') as f:
            f.write(config_content)

        # Set restrictive permissions on config file since it contains sensitive data
        config_file.chmod(0o600)
        logging.info(f"Created configuration file with restricted permissions (600): {config_file}")
        return True

    except (OSError, IOError) as e:
        logging.error(f"Configuration setup failed: {e}")
        return False

def setup_shell_scripts(no_prompt=False):
    """Setup shell integration scripts and configuration template."""
    if not prompt_user("\nAbout to add abc files to $HOME/.local/share/ Continue?", no_prompt=no_prompt):
        print("Setup cancelled")
        return 0

    try:
        # Get package resources
        with importlib.resources.path('abc_cli', 'abc.sh') as shell_script:
            package_dir = shell_script.parent

        # Create ~/.local/share/abc
        share_dir = Path.home() / '.local' / 'share' / 'abc'
        share_dir.mkdir(parents=True, exist_ok=True)

        # Copy and update shell scripts
        venv_python = sys.executable  # Get virtualenv Python path
        scripts = ['abc.sh', 'abc.tcsh']
        for script in scripts:
            source = package_dir / script
            target = share_dir / script

            # Update Python path and copy
            with open(source, 'r') as f:
                content = f.read().replace('\\python3', f'\\{venv_python}')
            with open(target, 'w') as f:
                f.write(content)
            target.chmod(0o755)
            logging.info(f"Installed: {target}")

        # Copy configuration template
        template_source = package_dir / 'abc.conf.template'
        template_target = share_dir / 'abc.conf.template'
        shutil.copy2(template_source, template_target)
        logging.info(f"Installed: {template_target}")

        if not prompt_user("\nAbout to add abc commands to shell rc files. Continue?", no_prompt=no_prompt):
            print("Setup cancelled")
            return 0

        # Update shell rc files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        modified = False
        found_shells = []

        for shell, rc_file in SHELL_RC_FILES.items():
            source_line = f'source "{share_dir}/abc.{shell if shell == "tcsh" else "sh"}"'
            rc_path = Path.home() / rc_file
            if not rc_path.exists():
                continue
            found_shells.append(shell)

            if try_modify_rc_file(rc_file, source_line, remove=False):
                modified = True

        if modified:
            print("\nShell configuration files have been updated.")

        if found_shells:
            print("\nTo activate the changes, either:")
            print("1. Start a new terminal, or")
            print("2. Run one of these commands in your current terminal:")
            for shell in found_shells:
                rc_file = SHELL_RC_FILES[shell]
                print(f"   For {shell}:  source ~/{rc_file}")

        # Set up configuration
        if not setup_config(no_prompt):
            print("\nWarning: Configuration setup failed. You will need to manually configure ~/.abc.conf")
            print(f"You can use {share_dir}/abc.conf.template as a template")

        return 0

    except (OSError, IOError) as e:
        logging.error(f"Setup failed: {e}")
        return 1

def uninstall(no_prompt=False):
    """Remove shell integration scripts and package files."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        modified = False
        found_shells = []

        if prompt_user("\nWould you like to remove abc shell integration files from ~/.local/share/abc?", default=True, no_prompt=no_prompt):
            # Remove ~/.local/share/abc directory
            share_dir = Path.home() / '.local' / 'share' / 'abc'
            if share_dir.exists():
                shutil.rmtree(share_dir)
                logging.info(f"Removed directory: {share_dir}")

        if prompt_user("\nWould you like to remove abc commands from your shell rc files?", default=True, no_prompt=no_prompt):
            # Remove source blocks from rc files
            for shell, rc_file in SHELL_RC_FILES.items():
                rc_path = Path.home() / rc_file
                if not rc_path.exists():
                    continue
                found_shells.append(shell)
                if try_modify_rc_file(rc_file, '', remove=True):
                    modified = True

        # Optionally remove configuration
        config_file = Path.home() / '.abc.conf'
        if config_file.exists() and prompt_user("\nWould you like to remove the configuration file (~/.abc.conf)?", default=False, no_prompt=no_prompt):
            # Create backup before removal since we know we'll modify it
            backup_file(config_file, timestamp)
            config_file.unlink()
            logging.info("Removed configuration file")

        print("\nUninstallation complete. You may now run:")
        print("pipx uninstall abc-cli")

        return 0

    except (OSError, IOError) as e:
        logging.error(f"Uninstall failed: {e}")
        return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup abc shell integration")
    parser.add_argument('--uninstall', action='store_true',
                      help="Remove shell integration scripts")
    parser.add_argument('--no-prompt', action='store_true',
                      help="Skip all prompts and use default values")
    args = parser.parse_args()

    try:
        if args.uninstall:
            return uninstall(args.no_prompt)
        else:
            return setup_shell_scripts(args.no_prompt)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1

if __name__ == '__main__':
    sys.exit(main())
