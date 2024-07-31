alias abc 'set __abc_cmd=`abc_generate --shell tcsh \!*`; \
  set __abc_prompt="`tcsh -i < /dev/null | sed s/exit//`"; \
  set __abc_tmpfile=`mktemp /tmp/__abc_$$.XXXXXX`; \
  python3 -c "from prompt_toolkit import prompt;from prompt_toolkit.formatted_text import ANSI;import termios,sys;termios.tcflush(sys.stdin,termios.TCIFLUSH);a=sys.argv;open(a[3],'\''w'\'').write(prompt(ANSI(a[1]),default=a[2]))" "$__abc_prompt" "$__abc_cmd" "$__abc_tmpfile"; \
  set __abc_user_cmd=`cat $__abc_tmpfile`; \
  date +"#+%s" > $__abc_tmpfile; \
  echo "$__abc_user_cmd" >> $__abc_tmpfile; \
  history -M $__abc_tmpfile; \
  rm -f $__abc_tmpfile; \
  eval $__abc_user_cmd; \
  unset __abc_cmd __abc_prompt __abc_tmpfile __abc_user_cmd'
