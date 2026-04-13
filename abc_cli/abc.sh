abc() {
    # Check for --help and --version options for direct passthrough
    if [ $# -gt 0 ] && ([ "$1" = "--help" ] || [ "$1" = "--version" ]); then
        abc_generate "$@"
        return $?
    fi

    # Interactive editing needs read -i, read -t fractional timeouts, and ${PS1@P} (bash 4.4+).
    if [ -z "$ZSH_VERSION" ] && [ -n "$BASH_VERSION" ]; then
        if [ "${BASH_VERSINFO[0]}" -lt 4 ] || { [ "${BASH_VERSINFO[0]}" -eq 4 ] && [ "${BASH_VERSINFO[1]}" -lt 4 ]; }; then
            echo "abc: bash $BASH_VERSION is too old; abc requires bash 4.4 or newer (or use zsh)." >&2
            echo "abc: on macOS, install a newer bash with: brew install bash" >&2
            return 1
        fi
    fi

    local shell=bash
    if [ -n "$ZSH_VERSION" ]; then
        shell=zsh
    fi
    local abc_cmd
    abc_cmd=$(abc_generate --shell $shell "$@")
    local abc_exit_code=$?
    if [ $abc_exit_code -ne 0 ]; then
        if [ -n "$abc_cmd" ]; then
            echo "$abc_cmd"
        fi
        return $abc_exit_code
    fi
    local user_cmd=$abc_cmd
    while read -t 0.1 -n 1; do : ; done
    if [ -n "$ZSH_VERSION" ]; then
        vared -p "$(print "$PS1")" -c user_cmd
        print -s "$user_cmd"
    else
        read -e -r -p "$(printf "%s" "${PS1@P}")" -i "$abc_cmd" user_cmd
        history -s $(history 1 | sed 's/^ *[0-9]* *//')
        history -s "$user_cmd"
    fi
    eval "$user_cmd"
}