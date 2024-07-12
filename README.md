# ABC (AI Bash Command)

ABC (AI Bash Command) is a command-line tool that uses AI to generate bash commands based on natural language descriptions. It leverages the power of large language models to interpret user intent and produce corresponding bash commands.

## Features

- Translates natural language descriptions into bash commands
- Configurable through a simple INI file
- Supports multiple configuration profiles
- Provides verbose and debug output options

## Quick Start

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up your configuration file at `~/.abc.conf`:
   ```ini
   [default]
   api_key = your_api_key_here
   ```

3. Run ABC:
   ```
   ./abc list all PDF files in the current directory
   ```

## Usage

```
abc [OPTION]... DESCRIPTION...
```

### Options

- `-c, --config CONFIGFILE`: Path to the configuration file
- `-s, --config-section SECTION`: Configuration section to use (default: "default")
- `--quiet`: Suppress all output except errors and generated commands
- `--verbose`: Provide detailed execution information
- `--debug`: Provide debug information
- `--version`: Display the program version and exit

### Examples

List all PDF files in the current directory:
```
abc list all PDF files in the current directory
```

Create a new directory and change into it:
```
abc 'create a new directory named "test" and cd into it'
```

## Configuration

ABC reads its configuration from an INI file. By default, it looks for `~/.abc.conf`, but you can specify a different file using the `--config` option or the `ABC_CONFIG` environment variable.

Example configuration:

```ini
[default]
api_key = your_default_api_key_here

[project-2]
api_key = your_project_specific_api_key_here
```

## TODO

- Allow user to indicate they want the commands to be run
- Support multiple LLM models
- Support multiple LLM providers

## Contributing

Pull requests and bug reports are unlikely to be reviewed, incorporated, or fixed, but you are welcome to fork the project and publish updates.

## License

This project is licensed under the Apache 2 License - see the [LICENSE](LICENSE) file for details.
