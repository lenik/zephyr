# bash completion for some_puff1

_some_puff1()
{
	local cur prev words cword
	_init_completion || return

	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '--dump --format --indent-size --color --help --version -d -f -C -h' -- "$cur"))
		return
	fi

	if [[ $prev == --indent-size ]]; then
		return
	fi

	if [[ $prev == --color || $prev == -C ]]; then
		COMPREPLY=($(compgen -W 'auto always never' -- "$cur"))
		return
	fi

	_filedir
}

complete -F _some_puff1 some_puff1
