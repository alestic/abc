# Installing abc (AI Bash Command)

This guide will walk you through the process of installing and setting up abc on your system.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- An API key for the Claude AI model from Anthropic
- bash 4.4 or higher, or zsh 5.0 or higher, or tcsh 6.0 or higher

## Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/alestic/abc.git
   cd abc
   ```

2. Build dependencies and install in $HOME/.local/bin/

   ```
   make build install
   ```

3. Add the following line to your shell configuration file:

   For bash users, add to `~/.bashrc`:
   ```bash
   source "$HOME/.local/bin/abc.sh"
   ```

   For zsh users, add to `~/.zshrc`:
   ```zsh
   source "$HOME/.local/bin/abc.sh"
   ```

   For tcsh users, add to `~/.tcshrc`:
   ```tcsh
   source "$HOME/.local/bin/abc.tcsh"
   ```

   Then, reload your shell configuration:

   For bash:
   ```bash
   source ~/.bashrc
   ```

   For zsh:
   ```zsh
   source ~/.zshrc
   ```

   For tcsh:
   ```tcsh
   source ~/.tcshrc
   ```

4. Create an Anthropic API key:

   https://console.anthropic.com/settings/keys

5. Create a configuration file at `~/.abc.conf` with your API key:
   ```ini
   [default]
   api_key = your_api_key_here
   ```

## Verifying the Installation

To verify that abc is installed correctly, run:

```
abc --version
```

This should display the version of abc.

## Updating

To update abc to the latest version, pull the latest changes from the repository and reinstall:

```
git pull
make build install
source ~/.bashrc  # or source ~/.zshrc for zsh users, or source ~/.tcshrc for tcsh users
```

## Uninstalling

To uninstall abc:

```
make uninstall
```

This will remove the abc_generate executable and the abc.sh and abc.tcsh scripts.

Don't forget to remove the `source` line from your `~/.bashrc`, `~/.zshrc`, or `~/.tcshrc` file.