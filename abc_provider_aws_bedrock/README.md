# abc-provider-aws-bedrock

AWS Bedrock LLM provider plugin for [abc-cli](https://github.com/alestic/abc). This provider enables abc to use AWS Bedrock's models for generating shell commands.

## Installation

```bash
# When installing abc-cli from GitHub
pipx inject abc-cli abc_provider_aws_bedrock@git+https://github.com/alestic/abc.git#subdirectory=abc_provider_aws_bedrock

# For development (from cloned repository)
pipx inject abc-cli -e ./abc_provider_aws_bedrock
```

## Configuration

Configure the provider in your `~/.abc.conf`:

```ini
[default]
provider = aws-bedrock
profile = abc-cli     # Optional: AWS credential profile name
region = us-east-1    # Optional: AWS region (default: us-east-1)
model = anthropic.claude-sonnet-4-20250514-v1:0  # Optional: Bedrock model ID
```

### Configuration Options

- `provider` (required): Must be set to `aws-bedrock`
- `profile` (optional): AWS credential profile name from `~/.aws/credentials`
  - If not specified, uses the default credential provider chain
  - See [AWS credentials configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- `region` (optional): AWS region where Bedrock is available. Default: `us-east-1`
- `model` (optional): The Bedrock model to use. Default: `anthropic.claude-sonnet-4-20250514-v1:0`
  - Currently supports Anthropic Claude models on Bedrock
- `temperature` (optional): Controls randomness in command generation. Default: `0.0`
  - Range: 0.0 to 1.0
  - Lower values produce more deterministic output
- `max_tokens` (optional): Maximum length of generated response. Default: `1000`

### AWS Authentication

The provider uses standard boto3 authentication mechanisms. No AWS credentials are stored in the abc configuration file - only an optional AWS profile name can be specified.

Authentication is resolved in this order:
1. If `profile` is specified in abc config, uses that named profile from `~/.aws/credentials`
2. Otherwise, uses the default credential provider chain:
   - Environment variables (AWS_ACCESS_KEY_ID, etc.)
   - Shared credential file (`~/.aws/credentials`)
   - IAM role when running on AWS resources

### AWS Setup

1. Ensure you have AWS credentials configured:
```bash
# Configure AWS CLI (if not already done)
aws configure
```

2. Create a specific profile for abc-cli (recommended):
```bash
aws configure --profile abc-cli
```

3. Enable Bedrock access in your AWS account:
   - Visit the [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
   - Request access to the Claude model
   - Configure IAM permissions for Bedrock

## Development

1. Clone the repository:
```bash
git clone https://github.com/alestic/abc.git
cd abc
```

2. Create and activate a virtual environment:
```bash
cd abc_provider_aws_bedrock
python3 -m venv venv
source venv/bin/activate
```

3. Install abc-cli and provider package with test dependencies:
```bash
# First install abc-cli in development mode
cd ..  # Back to abc root
pip install -e .

# Then install provider package with test dependencies
cd abc_provider_aws_bedrock
pip install -e ".[test]"
```

4. Run tests:
```bash
python3 -m pytest
```

### Testing

The provider includes tests to verify:
- Configuration parsing and validation
- AWS authentication handling
- Command generation functionality
- Error handling and edge cases
- Integration with abc-cli core

Tests use unittest.mock to mock AWS services, so no real AWS credentials are required for testing.

## License

Apache 2.0 - See [LICENSE](../LICENSE)
