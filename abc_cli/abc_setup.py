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

    prompt = f"{message} [{'YES' if default else 'yes'}/{'no' if default else 'NO'}/stop] "
    response = get_terminal_input(prompt, 'yes' if default else 'no')

    if not response:
        return default

    response = response.lower()
    if response in ['y', 'yes']:
        return True
    elif response in ['n', 'no']:
        return False
    else:
        print("\nSetup stopped by user")
        sys.exit(0)

def show_instructions_and_confirm(description, commands, no_prompt=False, default=True):
    """Show instructions and get confirmation.

    Args:
        description: Description of what will be done
        commands: List of commands or instructions
        no_prompt: Whether to skip confirmation
        default: Default response (True for YES, False for NO)

    Returns:
        bool: True if confirmed or no_prompt is True, False otherwise
    """
    print()
    print(description)
    print()
    print("Commands to run:")
    print("---------------")
    for cmd in commands:
        print(cmd)
    print()

    return prompt_user("Would you like me to perform these changes? (\"no\" means you have done them)", default=default, no_prompt=no_prompt)

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

def try_modify_rc_file(file_path, source_line, remove=False, no_prompt=False):
    """Check if modification is needed and perform it if required."""
    lines = read_rc_file(file_path)
    if lines is None:
        logging.info(f"Skipping {Path.home() / file_path}: file not found")
        return False

    if not check_needs_modification(lines, source_line, remove):
        logging.info(f"Skipping {Path.home() / file_path}: no modification needed")
        return False

    # Show what we're going to do
    rc_path = Path.home() / file_path
    if remove:
        description = f"About to remove abc block from {rc_path}"
        commands = [
            f"# Remove the following block from {rc_path}:",
            MARKER_BEGIN,
            MARKER_MIDDLE,
            "...",
            MARKER_END
        ]
    else:
        description = f"About to modify {rc_path}"
        commands = [
            f"# Add/update block in {rc_path} to:",
            MARKER_BEGIN,
            MARKER_MIDDLE,
            source_line,
            MARKER_END
        ]

    if not show_instructions_and_confirm(description, commands, no_prompt):
        return False

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = rc_path.with_suffix(f'.bak_{timestamp}')
    shutil.copy2(rc_path, backup_path)
    logging.info(f"Created backup: {backup_path}")

    if remove:
        new_lines, _ = remove_abc_block(lines)
        logging.info(f"Removing abc block from {rc_path}")
    else:
        try:
            existing_block, start, end = find_abc_block(lines)
            new_block = create_abc_block(source_line)
            if existing_block is not None:
                # Update existing block
                lines[start:end+1] = new_block
                logging.info(f"Updating abc block in {rc_path}")
            else:
                # Add new block
                if lines and lines[-1].strip():
                    lines.append('\n')  # Add newline if file doesn't end with one
                lines.extend(new_block)
                logging.info(f"Adding abc block to {rc_path}")
            new_lines = lines
        except ValueError as e:
            logging.error(f"Error processing {rc_path}: {str(e)}")
            return False

    write_rc_file(file_path, new_lines)
    return True

def get_config_paths():
    """Get config file paths following XDG Base Directory Specification."""
    # Legacy config path
    legacy_config = Path.home() / '.abc.conf'

    # XDG config path
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')
    xdg_config = Path(xdg_config_home) / 'abc' / 'config'

    return xdg_config, legacy_config

def setup_config(no_prompt=False, package_dir=None):
    """Set up abc configuration file with API key."""
    xdg_config, legacy_config = get_config_paths()

    # Check for legacy config when XDG config exists
    if xdg_config.exists() and legacy_config.exists():
        description = f"Found legacy config at ~/.abc.conf (deprecated)"
        commands = [
            "# Will remove legacy config (XDG config at ~/.config/abc/config is primary):",
            f"rm {legacy_config}"
        ]
        if show_instructions_and_confirm(description, commands, no_prompt):
            legacy_config.unlink()
            logging.info("Removed legacy configuration file")

    # Handle legacy config migration if XDG doesn't exist
    if not xdg_config.exists() and legacy_config.exists():
        description = "Found legacy config at ~/.abc.conf"
        commands = [
            "# Create parent directory:",
            f"mkdir -p {xdg_config.parent}",
            "",
            "# Copy config and set permissions:",
            f"cp {legacy_config} {xdg_config}",
            f"chmod 600 {xdg_config}",
            "# Add deprecation notice to old config"
        ]
        if show_instructions_and_confirm(description, commands, no_prompt):
            # Create XDG config directory
            xdg_config.parent.mkdir(parents=True, exist_ok=True)

            # Copy existing config to XDG location
            shutil.copy2(legacy_config, xdg_config)
            xdg_config.chmod(0o600)

            # Add deprecation warning to old config
            with open(legacy_config, 'r') as f:
                old_content = f.read()
            with open(legacy_config, 'w') as f:
                f.write("# This configuration file is deprecated and can be safely removed.\n")
                f.write(f"# Your configuration has been migrated to: {xdg_config}\n")
                f.write("# Please remove this file\n\n")
                f.write(old_content)

            logging.info(f"Migrated config to: {xdg_config}")
            return True

    # Check if XDG config exists
    if xdg_config.exists():
        description = f"Configuration file exists at {xdg_config}. Reconfigure?"
        commands = [
            "# Create parent directory if needed:",
            f"mkdir -p {xdg_config.parent}",
            "",
            "# Copy template and set permissions:",
            f"cp {package_dir}/abc.conf.template {xdg_config}",
            f"chmod 600 {xdg_config}",
            "",
            "# Then edit to add your API key:",
            f"$EDITOR {xdg_config}  # Add your API key from https://console.anthropic.com/settings/keys"
        ]
        if not show_instructions_and_confirm(description, commands, no_prompt, default=False):
            return True

    try:
        # Create XDG config directory
        xdg_config.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing XDG config if it exists
        if xdg_config.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file(xdg_config, timestamp)

        # Get the template content
        with importlib.resources.path('abc_cli', 'abc.conf.template') as template_path:
            with open(template_path, 'r') as f:
                template_content = f.read()

        # Show what we're going to do if creating new config
        if not xdg_config.exists():
            description = f"About to create configuration file at {xdg_config}"
            commands = [
                "# Create parent directory if needed:",
                f"mkdir -p {xdg_config.parent}",
                "",
                "# Copy template and set permissions:",
                f"cp {package_dir}/abc.conf.template {xdg_config}",
                f"chmod 600 {xdg_config}",
                "",
                "# Then edit to add your API key:",
                f"$EDITOR {xdg_config}  # Add your API key from https://console.anthropic.com/settings/keys"
            ]
            if not show_instructions_and_confirm(description, commands, no_prompt):
                return False

        # Prompt for API key if interactive
        print("\nPlease enter your Anthropic API key", file=sys.stderr)
        print("(You can get this from https://console.anthropic.com/settings/keys)", file=sys.stderr)
        api_key = get_terminal_input("API key: ", '{ANTHROPIC_API_KEY}', sensitive=True)

        # Write configuration
        config_content = template_content.replace('{ANTHROPIC_API_KEY}', api_key)
        with open(xdg_config, 'w') as f:
            f.write(config_content)

        # Set restrictive permissions on config file since it contains sensitive data
        xdg_config.chmod(0o600)
        logging.info(f"Created configuration file with restricted permissions (600): {xdg_config}")
        return True

    except (OSError, IOError) as e:
        logging.error(f"Configuration setup failed: {e}")
        return False

def setup_shell_scripts(no_prompt=False):
    """Setup shell integration scripts and configuration template."""
    try:
        # Get package resources
        with importlib.resources.path('abc_cli', 'abc.sh') as shell_script:
            package_dir = shell_script.parent

        # Show what we're going to do
        share_dir = Path.home() / '.local' / 'share' / 'abc'
        description = "About to set up abc shell integration"
        commands = [
            f"# Create directory:",
            f"mkdir -p {share_dir}",
            "",
            "# Install shell scripts with execute permissions:",
            f"cp {package_dir}/abc.sh {share_dir}/abc.sh",
            f"cp {package_dir}/abc.tcsh {share_dir}/abc.tcsh",
            f"chmod 755 {share_dir}/abc.sh",
            f"chmod 755 {share_dir}/abc.tcsh",
            "",
            "# Copy config template:",
            f"cp {package_dir}/abc.conf.template {share_dir}/abc.conf.template"
        ]
        if show_instructions_and_confirm(description, commands, no_prompt):
            # Create ~/.local/share/abc
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

        # Update shell rc files
        modified = False
        found_shells = []

        for shell, rc_file in SHELL_RC_FILES.items():
            source_line = f'source "{share_dir}/abc.{shell if shell == "tcsh" else "sh"}"'
            rc_path = Path.home() / rc_file
            if not rc_path.exists():
                continue
            found_shells.append(shell)

            if try_modify_rc_file(rc_file, source_line, remove=False, no_prompt=no_prompt):
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
        if not setup_config(no_prompt, package_dir):
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

        # Show shell integration removal instructions
        share_dir = Path.home() / '.local' / 'share' / 'abc'
        if share_dir.exists():
            description = "About to remove abc shell integration files"
            commands = [
                f"# Remove directory and contents:",
                f"rm -rf {share_dir}"
            ]
            if show_instructions_and_confirm(description, commands, no_prompt):
                shutil.rmtree(share_dir)
                logging.info(f"Removed directory: {share_dir}")

        # Show RC file cleanup instructions
        description = "About to remove abc commands from shell RC files"
        commands = ["# Will remove abc blocks from:"]
        for shell, rc_file in SHELL_RC_FILES.items():
            rc_path = Path.home() / rc_file
            if rc_path.exists():
                commands.append(f"- ~/{rc_file}")
        if show_instructions_and_confirm(description, commands, no_prompt):
            for shell, rc_file in SHELL_RC_FILES.items():
                rc_path = Path.home() / rc_file
                if not rc_path.exists():
                    continue
                found_shells.append(shell)
                if try_modify_rc_file(rc_file, '', remove=True, no_prompt=no_prompt):
                    modified = True

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
