abc() {
    if [[ "$1" == --* ]]; then
        command abc_generate "$@" # Pass all arguments
        return $?                # Exit with abc_generate's status
    fi
    local shell=bash
    if [ -n "$ZSH_VERSION" ]; then
        shell=zsh
    fi
    local abc_cmd=$(command abc_generate --shell "$shell" "$@")
    local exit_status=$?

    if [ $exit_status -ne 0 ]; then
        return $exit_status
    fi
    if [ -z "$abc_cmd" ]; then
        # abc_generate succeeded but produced no command (e.g. handled info already)
        return 0
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
    if [ -n "$user_cmd" ]; then
        eval "$user_cmd"
    else
        return 0 # Or appropriate status if user clears the command
    fi
}