# bash completion for puff1

_puff1()
{
	local cur prev words cword
	_init_completion || return

	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '--verbose --quiet --help --version' -- "$cur"))
		return
	fi

	_filedir
}

complete -F _puff1 puff1
