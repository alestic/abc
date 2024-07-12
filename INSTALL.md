# Installing abc (AI Bash Command)

This guide will walk you through the process of installing and setting up ABC on your system.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- An API key for the Claude AI model from Anthropic

## Installation Steps

1. Clone the repository or download the source code:
   ```
   git clone https://github.com/ehammmond/abc.git
   cd abc
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a configuration file at `~/.abc.conf` with your API key:
   ```ini
   [default]
   api_key = your_api_key_here
   ```

4. (Optional) Add the abc directory to your PATH for easier access:
   ```
   echo 'export PATH=$PATH:/path/to/abc' >> ~/.bashrc
   source ~/.bashrc
   ```

## Verifying the Installation

To verify that ABC is installed correctly, run:

```
./abc --version
```

This should display the version number of ABC.

## Troubleshooting

If you encounter any issues during installation, please check the following:

1. Ensure you have the correct Python version installed:
   ```
   python3 --version
   ```

2. Verify that all required packages are installed:
   ```
   pip list
   ```

3. Check that your configuration file is correctly formatted and contains a valid API key.

## Updating

To update ABC to the latest version, pull the latest changes from the repository and reinstall the requirements:

```
git pull origin main
pip install -r requirements.txt
```

## Uninstalling

To uninstall ABC, simply delete the directory containing the script and remove the configuration file:

```
rm -rf /path/to/abc
rm ~/.abc.conf
```

If you added abc to your PATH, remember to remove that line from your `.bashrc` file as well.