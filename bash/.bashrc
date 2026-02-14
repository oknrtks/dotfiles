# ~/.bashrc: executed by bash(1) for non-login shells.

# Note: PS1 and umask are already set in /etc/profile. You should not
# need this unless you want different defaults for root.
# PS1='${debian_chroot:+($debian_chroot)}\h:\w\$ '
# umask 022

# You may uncomment the following lines if you want `ls' to be colorized:
# export LS_OPTIONS='--color=auto'
# eval "$(dircolors)"
# alias ls='ls $LS_OPTIONS'
# alias ll='ls $LS_OPTIONS -l'
# alias l='ls $LS_OPTIONS -lA'
#
# Some more alias to avoid making mistakes:
# alias rm='rm -i'
# alias cp='cp -i'
# alias mv='mv -i'

# export LC_ALL=ja_JP.UTF-8
# export LANG=ja_JP.UTF-8alias ls='ls --color=auto'
alias ls='ls --color=auto'
alias ll='ls -l'
alias la='ls -la'
alias update-uv='curl -LsSf https://astral.sh/uv/install.sh | sh'
alias gemini-ask-uvx='uvx git+https://github.com/oknrtks/gemini-ask'
alias yahoo-search-uvx='uvx git+https://github.com/oknrtks/yahoo-search'
[ -f ~/.bash_local ] && . ~/.bash_local

. "$HOME/.local/bin/env"
