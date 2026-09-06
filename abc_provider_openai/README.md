# OpenAI Provider for abc

[Created by AI: Claude Code, Codex with GPT-6 Astra]

This package provides OpenAI/ChatGPT integration for the abc (AI Bash Command) tool.

## Installation

This provider is typically installed as part of the main abc tool:

```bash
# Development install
make install-dev

# Or install directly
pipx inject abc-cli abc-provider-openai
```

## Configuration

Add an OpenAI configuration section to your `~/.abc.conf` file:

```ini
[default]
provider = openai
api_key = {OPENAI_API_KEY}
model = gpt-6-astra
reasoning_effort = low

[gpt-4o]
provider = openai
api_key = {OPENAI_API_KEY}
model = gpt-4o
```

### Supported Models

- `gpt-6-astra` (default)
- `gpt-5`
- `gpt-4o`
- `gpt-4-turbo`
- Other OpenAI chat completion models

### Configuration Options

- `provider`: Must be "openai"
- `api_key`: Your OpenAI API key (required)
- `model`: Model to use (optional, defaults to gpt-6-astra)
- `temperature`: Sampling temperature 0.0-2.0 (optional, default: 0.0, omitted for newer models that don't support 0.0)
- `max_tokens`: Maximum response tokens (optional, default: 4096, including reasoning tokens). A response cut off at this limit is an error, not a partial command.
- `timeout`: Request timeout in seconds (optional, default: 120)
- `organization`: OpenAI organization ID (optional)
- `reasoning_effort`: Reasoning effort, sent whenever set: none, minimal, low, medium, high, xhigh, max (optional, default: low for Astra, minimal for GPT-5 models, otherwise the API default; set it empty to use the API default on GPT-5 too)
- `api`: OpenAI API to call, `chat_completions` or `responses` (optional, default: chat_completions)

## Usage

Once configured, use abc with your OpenAI configuration:

```bash
# Use default config
abc "list files by size"

# Use specific config section
abc --use gpt-4o "find large files"
```

## API Key Setup

Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys) and either:

1. Set it in your config file: `api_key = sk-your-key-here`
2. Set environment variable: `export OPENAI_API_KEY=sk-your-key-here`

## Testing

Run the provider tests:

```bash
python -m pytest abc_provider_openai/tests/
```

## Requirements

- Python 3.8+
- OpenAI Python SDK 1.0+
- Valid OpenAI API key
