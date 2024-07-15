abc() {
    local abc_cmd=$(abc_generate "$@")
    read -e -r -p "$(printf "%s" "${PS1@P}")" -i "$abc_cmd" user_cmd
    history -s $(history 1 | sed 's/^ *[0-9]* *//')
    history -s "$user_cmd"
    eval "$user_cmd"
}