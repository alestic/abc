abc() {
    local shell=bash
    if [ -n "$ZSH_VERSION" ]; then
        shell=zsh
    fi
    local abc_cmd=$(abc_generate --shell $shell "$@")
    local user_cmd=$abc_cmd
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