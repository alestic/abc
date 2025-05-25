# Installing abc (AI bash/zsh/tcsh Command)

This guide provides instructions for installing abc on your system using pipx.

## Prerequisites

- Linux or macOS
- Python 3.8 or higher
- bash 4.4+, zsh 5.0+, or tcsh 6.0+
- An API key for your chosen LLM provider (default: Anthropic)

## LLM Providers

abc uses a plugin system for LLM providers. The default installation includes:

- Anthropic LLM provider (Claude)

Additional providers can be installed using:
```bash
pipx inject abc-cli abc-provider-NAME
```

## Easy Installation

1. Install the latest version of abc from GitHub using pipx:

   ```bash
   curl -fsSL https://getabc.sh/ | bash
   ```

   This will:
   - Prompt you before every action
   - Create backups of any modified files
   - Describe every change it makes
   - Install pipx using the method preferred by your OS
   - Install the abc app using pipx
   - Install abc shell integration scripts
   - Add an abc command block to your shell rc file(s)
   - Guide you through LLM API key setup
   - Create the abc configuration file

2. Start a new terminal or reload your shell rc file to enable the abc command:

   ```bash
   # For bash:
   source ~/.bashrc

   # For zsh:
   source ~/.zshrc

   # For tcsh:
   source ~/.tcshrc
   ```

3. Verify the installation:

   ```bash
   abc hi
   abc --version
   ```

## Manual Installation

1. Install pipx, if you haven't already:

   ```bash
   # macOS
   brew install pipx
   pipx ensurepath

   # Ubuntu 23.04 or above
   sudo apt install pipx
   pipx ensurepath

   # Fedora
   sudo dnf install pipx
   pipx ensurepath

   # Arch
   sudo pacman -S python-pipx
   pipx ensurepath

   # Alternative: using pip
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   ```

2. Install abc using pipx:

   From GitHub:

   ```bash
   pipx install git+https://github.com/alestic/abc.git
   pipx inject abc-cli abc-provider-anthropic@git+https://github.com/alestic/abc.git#subdirectory=abc_provider_anthropic
   abc_setup
   ```

   Alternative (for development):

   ```bash
   git clone https://github.com/alestic/abc.git
   cd abc
   pipx install -e .
   pipx inject abc-cli -e ./abc_provider_anthropic
   pipx inject abc-cli -e ./abc_provider_aws_bedrock
   abc_setup
   ```

3. Start a new terminal or reload your shell rc file to enable the abc command:

   ```bash
   # For bash:
   source ~/.bashrc

   # For zsh:
   source ~/.zshrc

   # For tcsh:
   source ~/.tcshrc
   ```

4. Verify the installation:

   ```bash
   abc hi
   abc --version
   ```

## Updating

To update abc to the latest version:

```bash
pipx upgrade abc-cli
abc_setup
```

## Uninstalling

To remove abc from your system:

```bash
abc_setup --uninstall
pipx uninstall abc-cli
```

## Files and Locations

- Shell integration: `~/.local/share/abc/`
- Shell configuration:
  - bash: `~/.bashrc`
  - zsh: `~/.zshrc`
  - tcsh: `~/.tcshrc`
- abc Configuration: `~/.abc.conf`

## Configuration

The configuration file (`~/.abc.conf`) supports multiple named sections for different LLM providers:

```ini
[default]
provider = anthropic
api_key = {ANTHROPIC_API_KEY}
model = claude-sonnet-4-20250514

[o1]  # OpenAI o1 config
provider = openai
api_key = {OPENAI_API_KEY}
model = o1
```

Each section requires:
- `provider`: The LLM provider to use (e.g., 'anthropic', 'openai')
- `api_key`: The API key for the provider

Optional settings:
- `model`: The specific model to use (defaults to provider's default)
- Additional provider-specific settings (see provider documentation)

Use different configurations with the --use option:
```bash
# Use default config
abc "list files by size"

# Use OpenAI o1 config
abc --use o1 "list files by size"
```

## Troubleshooting

1. If you see "command not found: pipx" during installation:
   - Run: `pipx ensurepath`
   - Start a new terminal

2. If abc commands don't work after installation:
   - Ensure your shell rc file was sourced
   - Check that `~/.abc.conf` exists and contains your API key
   - Verify the shell integration with `type abc`

3. For other issues:
   - Check the error message
   - Verify Python version: `python3 --version`
   - Ensure shell version meets requirements
