#!/bin/bash
# abc/install_from_github.sh - Install pipx and use to install abc from GitHub
# [Created with AI: Codex with GPT-6 Astra]

set -e  # Exit on error
set -u  # Exit on undefined variable

# Default values
NO_PROMPT=false
NO_PROMPT_OPTION=
FORCE=false
FORCE_OPTION=

# List of providers to install/upgrade
PROVIDERS=(
    "anthropic"
    "aws_bedrock"
    "openai"
)

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-prompt)
            NO_PROMPT=true
            NO_PROMPT_OPTION="--no-prompt"
            shift
            ;;
        --force)
            FORCE=true
            FORCE_OPTION="--force"
            shift
            ;;
        *)
            error "Unknown argument: $1"
            ;;
    esac
done

# Logging setup
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [abc] [INFO] $1"
}

error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [abc] [ERROR] $1" >&2
    exit 1
}

is_interactive() {
    # Check if stderr is connected to a terminal
    # This works even when stdin is a pipe
    [[ -t 2 ]]
}

prompt_user() {
    local message=$1
    local default=${2:-"yes"}  # Default to yes if not specified

    # Skip prompt if --no-prompt flag is set or not interactive
    if $NO_PROMPT || ! is_interactive; then
        echo "$default"
        return
    fi

    # Prompt user on stderr to avoid pipe interference
    local prompt
    if [ "$default" = "yes" ]; then
        prompt=" [YES/no/stop] "
    else
        prompt=" [yes/NO/stop] "
    fi

    echo -n "$message$prompt" >&2
    read -r response </dev/tty  # Read directly from terminal

    # Add newline since we used echo -n above
    echo >&2

    response=$(printf '%s' "$response" | tr '[:upper:]' '[:lower:]')

    if [[ -z "$response" ]]; then
        echo "$default"
    elif [[ "$response" =~ ^(yes|y)$ ]]; then
        echo "yes"
    elif [[ "$response" =~ ^(no|n)$ ]]; then
        echo "no"
    else
        log "Installation stopped by user"
        exit 1  # Exit with error to prevent "Installation completed successfully!"
    fi
}

# Helper function to show instructions and get confirmation
show_instructions_and_confirm() {
    local description=$1
    local commands=$2
    local requires_sudo=${3:-false}
    local default=${4:-"yes"}

    echo
    echo "$description"
    if [[ "$requires_sudo" == true ]]; then
        echo "(requires sudo access)"
    fi
    echo
    echo "Commands to run:"
    echo "---------------"
    echo "$commands"
    echo

    local response
    response=$(prompt_user "Would you like me to perform these changes? (\"no\" means you have done them)" "$default")
    if [[ "$response" = "yes" ]]; then
        return 0
    elif [[ "$response" = "no" ]]; then
        return 1
    else
        # Should never get here since prompt_user exits on stop
        exit 1
    fi
}

install_pipx() {
    local package_manager=""
    local install_command=""
    local requires_sudo=false
    local extra_command=""
    local commands=""

    # Detect OS and set up commands
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            package_manager="Homebrew"
            commands="brew install pipx"
            install_command="brew install pipx"
        else
            error "Homebrew not found. Please install Homebrew first."
        fi
    elif command -v apt &> /dev/null; then
        package_manager="apt"
        commands="sudo apt update\nsudo apt install -y pipx"
        requires_sudo=true
        extra_command="sudo apt update"
        install_command="sudo apt install -y pipx"
    elif command -v dnf &> /dev/null; then
        package_manager="dnf"
        commands="sudo dnf install -y pipx"
        requires_sudo=true
        install_command="sudo dnf install -y pipx"
    elif command -v pacman &> /dev/null; then
        package_manager="pacman"
        commands="sudo pacman -S --noconfirm python-pipx"
        requires_sudo=true
        install_command="sudo pacman -S --noconfirm python-pipx"
    elif command -v yum &> /dev/null; then
        package_manager="yum"
        commands="sudo yum install -y python3-pip\npython3 -m pip install --user pipx"
        requires_sudo=true
        install_command="sudo yum install -y python3-pip && python3 -m pip install --user pipx"
    else
        package_manager="pip"
        commands="python3 -m pip install --user pipx"
        install_command="python3 -m pip install --user pipx"
    fi
    commands+="\npipx ensurepath"

    # Show instructions and get confirmation
    if show_instructions_and_confirm \
        "About to install pipx using $package_manager" \
        "$(echo -e "$commands")" \
        "$requires_sudo" \
        "yes"; then
        # Execute commands
        if [[ -n "$extra_command" ]]; then
            eval "$extra_command" || error "Failed to update package database"
        fi
        eval "$install_command" || error "Failed to install pipx"
    fi
}

install_abc() {
    local commands="pipx install git+https://github.com/alestic/abc.git"
    commands+="\n\n# Then install providers:"
    for provider in "${PROVIDERS[@]}"; do
        commands+="\npipx inject abc-cli abc-provider-${provider}@git+https://github.com/alestic/abc.git#subdirectory=abc_provider_${provider}"
    done

    # Show instructions and get confirmation
    if show_instructions_and_confirm \
        "About to install abc and providers" \
        "$(echo -e "$commands")" \
        "false" \
        "yes"; then
        # Execute commands
        output=$(pipx install git+https://github.com/alestic/abc.git $FORCE_OPTION 2>&1)
        echo "$output"
        if [ $? -eq 0 ]; then
            log "Installation successful"
        elif echo "$output" | grep -q "installed package abc-cli"; then
            log "Installation successful despite pipx warning"
        else
            error "Failed to install abc via pipx"
        fi

        # Install providers
        for provider in "${PROVIDERS[@]}"; do
            log "Installing ${provider} provider..."
            output=$(pipx inject abc-cli abc-provider-${provider}@git+https://github.com/alestic/abc.git#subdirectory=abc_provider_${provider} $FORCE_OPTION 2>&1)
            echo "$output"
            if [ $? -ne 0 ] && ! echo "$output" | grep -q "injected package"; then
                error "Failed to install ${provider} provider"
            fi
        done
    fi
}

upgrade_abc() {
    local commands="pipx upgrade abc-cli"
    commands+="\n\n# Then upgrade providers:"
    for provider in "${PROVIDERS[@]}"; do
        commands+="\npipx inject abc-cli abc-provider-${provider}@git+https://github.com/alestic/abc.git#subdirectory=abc_provider_${provider}"
    done

    # Show instructions and get confirmation
    if show_instructions_and_confirm \
        "About to upgrade abc and providers" \
        "$(echo -e "$commands")" \
        "false" \
        "yes"; then
        # Execute commands
        output=$(pipx upgrade abc-cli 2>&1)
        echo "$output"
        if [ $? -eq 0 ]; then
            log "Upgrade successful"
        elif echo "$output" | grep -q "upgraded package abc-cli"; then
            log "Upgrade successful despite pipx warning"
        else
            error "Failed to upgrade abc"
        fi

        # Upgrade providers
        for provider in "${PROVIDERS[@]}"; do
            log "Upgrading ${provider} provider..."
            output=$(pipx inject abc-cli abc-provider-${provider}@git+https://github.com/alestic/abc.git#subdirectory=abc_provider_${provider} $FORCE_OPTION 2>&1)
            echo "$output"
            if [ $? -ne 0 ] && ! echo "$output" | grep -q "injected package"; then
                error "Failed to upgrade ${provider} provider"
            fi
        done
    fi
}

main() {
    log "Starting abc installation from GitHub..."

    # Check if pipx is already installed
    if command -v pipx &> /dev/null; then
        log "pipx is already installed"
    else
        log "pipx not found. Installation required."
        install_pipx
    fi

    # Ensure pipx is in PATH
    log "Ensuring pipx apps are in PATH..."
    pipx ensurepath || error "Failed to ensure pipx apps are in PATH"

    # Handle abc installation/upgrade
    if pipx list 2>/dev/null | grep -q "abc-cli"; then
        log "abc is already installed, attempting upgrade..."
        upgrade_abc
    else
        log "Installing abc from GitHub..."
        install_abc
    fi

    # Run abc setup in a login shell to get updated PATH
    log "Running abc setup..."
    if show_instructions_and_confirm \
        "About to run abc setup" \
        "bash -l -c \"abc_setup $NO_PROMPT_OPTION\"" \
        "false" \
        "yes"; then
        bash -l -c "abc_setup $NO_PROMPT_OPTION" || error "Failed to run abc setup"
    fi

    log "Installation completed successfully!"

    # Consume any remaining input to prevent curl write errors when piped from web
    cat > /dev/null 2>/dev/null || true
}

# Handle interrupts gracefully
trap 'echo -e "\nInstallation cancelled by user"; exit 1' INT

main "$@"
