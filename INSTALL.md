# Installing abc (AI Bash Command)

This guide will walk you through the process of installing and setting up abc on your system.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- An API key for the Claude AI model from Anthropic

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

3. Add the following line to your `~/.bashrc`:

```bash
source "$HOME/.local/bin/abc.sh"
```

Then, reload your shell configuration:

```bash
source ~/.bashrc
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
abc_generate --version
```

This should display the version of abc_generate.

## Updating

To update abc to the latest version, pull the latest changes from the repository and reinstall:

```
git pull
make build install
source ~/.bashrc
```

## Uninstalling

To uninstall abc:

```
make uninstall
```

This will remove the abc_generate executable and the abc.sh script.