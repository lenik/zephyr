# bash completion for zephyr and related wrappers
# SPDX-License-Identifier: AGPL-3.0-or-later

_zephyr_langs='bash c clib cs erlang go haskell java perl python rust smalltalk swift typescript'
_zephyr_cmds='create rename add remove detect help'

_zephyr()
{
	local cur prev words cword
	_init_completion || return

	local cmd=
	local i
	for ((i = 1; i < cword; i++)); do
		case "${words[i]}" in
			create|rename|add|remove|detect|help)
				cmd="${words[i]}"
				break
				;;
		esac
	done

	if [[ -z $cmd ]]; then
		if [[ $cur == -* ]]; then
			COMPREPLY=($(compgen -W '--help --version' -- "$cur"))
		else
			COMPREPLY=($(compgen -W "$_zephyr_cmds" -- "$cur"))
		fi
		return
	fi

	case $cmd in
		create)
			case $prev in
				-l|--lang)
					COMPREPLY=($(compgen -W "$_zephyr_langs" -- "$cur"))
					return
					;;
				-D|--distribution|-1|--init-version|-a|--author|-e|--email)
					COMPREPLY=()
					return
					;;
			esac
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '-l --lang -D --distribution -1 --init-version -a --author -e --email --help' -- "$cur"))
				return
			fi
			# project name / optional puff names: prefer directories for project
			_filedir -d
			;;
		rename|add|remove)
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '--help' -- "$cur"))
				return
			fi
			_filedir
			;;
		detect|help)
			COMPREPLY=()
			;;
	esac
}

_zephyr_create()
{
	local cur prev words cword
	_init_completion || return

	case $prev in
		-l|--lang)
			COMPREPLY=($(compgen -W "$_zephyr_langs" -- "$cur"))
			return
			;;
		-D|--distribution|-1|--init-version|-a|--author|-e|--email)
			COMPREPLY=()
			return
			;;
	esac
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-l --lang -D --distribution -1 --init-version -a --author -e --email --help' -- "$cur"))
		return
	fi
	_filedir -d
}

_zephyr_rename()
{
	local cur prev words cword
	_init_completion || return
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '--help' -- "$cur"))
		return
	fi
	_filedir
}

_zephyr_add()
{
	_zephyr_rename
}

_zephyr_remove()
{
	_zephyr_rename
}

complete -F _zephyr zephyr
complete -F _zephyr_create zephyr-create
complete -F _zephyr_rename zephyr-rename
complete -F _zephyr_add zephyr-add
complete -F _zephyr_remove zephyr-remove
