#!/usr/bin/env python3
"""
abc_generate - AI Bash Command Generator

Website, source code, and documentation:

  https://getabc.sh
  https://github.com/alestic/abc

Credits:

  Written by Claude 3.5 Sonnet
  Prompt crafting by Eric Hammond
"""

import argparse
import configparser
import logging
import os
import sys
from typing import Dict
import re
import distro
from importlib import metadata

from . import LLMProvider
from .prompts import get_system_prompt

# Entry point group for LLM providers
PROVIDER_ENTRY_POINT = 'abc.llm_providers'

VERSION: str = "abc (AI Bash Command) version 2024.12.30"
PROGRAM_NAME: str = "abc"

# Config file
DEFAULT_CONFIG_SECTION: str = 'default'
DEFAULT_PROVIDER: str = 'anthropic'

# Log format
LOG_FORMAT: str = f'%(asctime)s [{PROGRAM_NAME}] [%(levelname)s] %(message)s'
LOG_FORMAT_DATE: str = '%Y-%m-%d %H:%M:%S'

# Constants for danger level parsing
DANGER_LEVEL_PATTERN = r'##DANGERLEVEL=(\d)## (.+)$'
HIGH_DANGER_THRESHOLD = 2
DANGEROUS_PREFIX = '#DANGEROUS# '

def get_os_info() -> str:
    """Get formatted OS information."""
    system = distro.name(pretty=True)
    version = distro.version(pretty=True)
    return f"{system} {version}".strip() or "POSIX"

def setup_logging(log_level: int) -> None:
    """Set up logging configuration."""
    logging.basicConfig(level=log_level, format=LOG_FORMAT, datefmt=LOG_FORMAT_DATE)

def create_argument_parser() -> argparse.ArgumentParser:
    """Create an argument parser for command-line arguments."""
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description="abc - AI Bash Command Generator")
    parser.add_argument('-c', '--config', type=argparse.FileType('r'),
                        help='Path to configuration file')
    parser.add_argument('--version', action='version', version=VERSION,
                        help='Display the program version and exit')
    parser.add_argument('--shell', choices=['bash', 'zsh', 'tcsh'], default='bash',
                        help='Specify the shell to generate commands for (default: bash)')
    parser.add_argument('--use', metavar='SECTION',
                        help='Use specific configuration section (default: default)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--verbose', action='store_const',
                       const=logging.INFO, dest='log_level',
                       help='Provide detailed information about the program execution')
    group.add_argument('--debug', action='store_const',
                       const=logging.DEBUG, dest='log_level',
                       help='Provide debug information, use this only when troubleshooting')
    parser.set_defaults(log_level=logging.WARNING)

    parser.add_argument('description', nargs=argparse.REMAINDER,
                        help='English description of the desired shell command')
    return parser

def get_config_file() -> str:
    """Get config file path with XDG support."""
    # Check CLI override or environment variable first
    if config_override := os.environ.get('ABC_CONFIG'):
        return os.path.expanduser(config_override)

    # XDG config path
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    xdg_config = os.path.join(xdg_config_home, 'abc', 'config')

    # Legacy config path
    legacy_config = os.path.expanduser('~/.abc.conf')

    # If both configs exist, warn about legacy config
    if os.path.exists(xdg_config) and os.path.exists(legacy_config):
        print("Warning: Found both XDG config and legacy config.", file=sys.stderr)
        print(f"Please remove the legacy config: rm {legacy_config}", file=sys.stderr)

    # Return first existing config or default to XDG path
    return xdg_config if os.path.exists(xdg_config) else legacy_config

def get_config(config_file_path: str, section: str = DEFAULT_CONFIG_SECTION) -> Dict[str, str]:
    """Read and parse the configuration file, using the specified section."""
    config = configparser.ConfigParser()
    with open(config_file_path, 'r') as config_file:
        config.read_file(config_file)
    if len(config.sections()) == 0:
        raise configparser.Error(f"Error: No sections found in config file '{config_file_path}'")
    if section not in config:
        raise configparser.Error(f"Error: Section '{section}' not found in config file '{config_file_path}'")
    return dict(config[section])

def get_provider(config: Dict[str, str]) -> LLMProvider:
    """Get the configured LLM provider."""
    if 'provider' not in config:
        # Default to anthropic for backward compatibility
        provider_name = DEFAULT_PROVIDER
    else:
        provider_name = config['provider']

    try:
        # Handle both old (pre-3.10) and new entry_points API
        try:
            # New API (Python 3.10+)
            eps = metadata.entry_points().select(group=PROVIDER_ENTRY_POINT)
            provider_ep = next(ep for ep in eps if ep.name == provider_name)
        except AttributeError:
            # Old API (Python < 3.10)
            eps = metadata.entry_points().get(PROVIDER_ENTRY_POINT, [])
            provider_ep = next(ep for ep in eps if ep.name == provider_name)

        # Load the provider class
        provider_class = provider_ep.load()
        return provider_class(config)

    except (StopIteration, metadata.PackageNotFoundError):
        raise ValueError(
            f"Provider '{provider_name}' not found. "
            f"Please install abc-provider-{provider_name} package."
        )

def process_generated_command(command: str) -> str:
    """Process the generated command based on its danger level.
    Also handles special markup like CDATA tags and markdown code blocks from certain LLM providers."""
    # First strip markdown code block delimiters (lines starting with ```)
    lines = command.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith('```')]
    command = '\n'.join(filtered_lines).strip()
    
    # Then strip any CDATA wrapper if present
    cdata_pattern = r'<!\[CDATA\[(.*?)\]\]>'
    if re.search(cdata_pattern, command, re.DOTALL):
        command = re.sub(cdata_pattern, r'\1', command, flags=re.DOTALL).strip()

    lines = command.splitlines()
    if not lines:
        return command  # Empty command, return as is

    # Check if the last line contains danger level information
    danger_match = re.match(DANGER_LEVEL_PATTERN, lines[-1])
    if not danger_match:
        return command  # No danger level provided or invalid format, return as is

    command_lines = lines[:-1]  # All lines except the last one
    danger_level = int(danger_match.group(1))
    justification = danger_match.group(2)

    if danger_level >= HIGH_DANGER_THRESHOLD:
        print(f"Warning: This command is potentially dangerous. {justification}", file=sys.stderr)
        command_lines[0] = f"{DANGEROUS_PREFIX}{command_lines[0]}"

    return '\n'.join(command_lines)

def main() -> int:
    try:
        parser = create_argument_parser()
        args = parser.parse_args()

        setup_logging(args.log_level)

        config_file_path = args.config.name if args.config else get_config_file()
        section = args.use if args.use else DEFAULT_CONFIG_SECTION
        config = get_config(config_file_path, section)

        logging.info(f"Using configuration section: {section}")

        # Get provider and validate config against schema
        provider = get_provider(config)
        schema = provider.get_config_schema()
        required_fields = schema.get('required', [])

        for field in required_fields:
            if field not in config:
                raise ValueError(f"{field} not found in configuration section '{section}'")

        description = " ".join(args.description)
        if not description:
            raise ValueError("No description provided")

        logging.info(f"Generating {args.shell} command for: {description}")

        # Set up context
        context = {
            'shell': args.shell,
            'os_info': get_os_info()
        }

        # Generate command
        raw_command = provider.generate_command(
            description=description,
            context=context,
            system_prompt=get_system_prompt(context)
        )

        processed_command = process_generated_command(raw_command)
        print(processed_command)

        return 0

    except (ValueError, configparser.Error) as e:
        logging.error(f"{e}")
        return 1
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
