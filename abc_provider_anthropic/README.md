# abc-provider-anthropic

Anthropic LLM provider for [abc-cli](https://github.com/alestic/abc). This provider enables abc to use Anthropic's Claude models for generating shell commands.

## Installation

The provider is included by default when installing abc-cli. If you need to install it separately:

```bash
# When installing abc-cli from GitHub
pipx inject abc-cli abc-provider-anthropic@git+https://github.com/alestic/abc.git#subdirectory=abc_provider_anthropic

# For development (from cloned repository)
pipx inject abc-cli -e ./abc_provider_anthropic
```

## Configuration

Configure the provider in your `~/.abc.conf`:

```ini
[default]
api_key = {ANTHROPIC_API_KEY}  # Required: Your Anthropic API key

# Optional settings with defaults shown:
model = claude-sonnet-4-20250514  # Claude model to use
temperature = 0.0                    # Lower values = more deterministic output
max_tokens = 1000                    # Maximum response length
```

### Configuration Options

- `api_key` (required): Your Anthropic API key. Get it from the [Anthropic Console](https://console.anthropic.com/settings/keys).
- `model` (optional): The Claude model to use. Default: `claude-sonnet-4-20250514`
  - Supported models: See [Anthropic's model list](https://docs.anthropic.com/claude/docs/models-overview)
- `temperature` (optional): Controls randomness in command generation. Default: `0.0`
  - Range: 0.0 to 1.0
  - Lower values produce more deterministic output
  - Higher values allow more creative variations
- `max_tokens` (optional): Maximum length of generated response. Default: `1000`

## Development

1. Clone the repository:
```bash
git clone https://github.com/alestic/abc.git
cd abc
```

2. Create and activate a virtual environment for development:
```bash
# Install python3-venv if needed
sudo apt install python3-venv

# Create virtual environment
cd abc_provider_anthropic
python3 -m venv venv
source venv/bin/activate
```

3. Install abc-cli and provider package with test dependencies:
```bash
# First install abc-cli in development mode
cd ..  # Back to abc root
pip install -e .

# Then install provider package with test dependencies
cd abc_provider_anthropic
pip install -e ".[test]"
```

4. Run tests:
```bash
python3 -m pytest
```

### Testing

The provider includes tests to verify:
- Configuration parsing and validation
- Command generation functionality
- Error handling and edge cases
- Integration with the abc-cli core

Note: Always run tests in the virtual environment. If you see "No module named pytest", ensure you've:
1. Activated the virtual environment with `source venv/bin/activate`
2. Installed test dependencies with `pip install -e ".[test]"`

## License

Apache 2.0 - See [LICENSE](../LICENSE)
