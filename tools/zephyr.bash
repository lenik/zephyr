# bash completion for zephyr and related wrappers
# SPDX-License-Identifier: AGPL-3.0-or-later

_zephyr_langs='bash c clib cpp cpplib csharp erlang go haskell java perl python ruby rust smalltalk swift typescript'
_zephyr_cmds='create rename add remove about version lint detect help'

_zephyr()
{
	local cur prev words cword
	_init_completion || return

	local cmd=
	local i
	for ((i = 1; i < cword; i++)); do
		case "${words[i]}" in
			create|rename|add|remove|about|version|lint|detect|help)
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
		about)
			case $prev in
				--color)
					COMPREPLY=($(compgen -W 'auto always never' -- "$cur"))
					return
					;;
			esac
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '-d --debian -r --redhat --color --help' -- "$cur"))
			fi
			;;
		version)
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '-g --git -c --changelog -r --rpm --help' -- "$cur"))
			fi
			;;
		lint)
			case $prev in
				--color)
					COMPREPLY=($(compgen -W 'auto always never' -- "$cur"))
					return
					;;
			esac
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '-v --verbose -q --quiet --strict --color --help' -- "$cur"))
			fi
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

_zephyr_about()
{
	local cur prev words cword
	_init_completion || return
	case $prev in
		--color)
			COMPREPLY=($(compgen -W 'auto always never' -- "$cur"))
			return
			;;
	esac
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-d --debian -r --redhat --color --help' -- "$cur"))
	fi
}

_zephyr_version()
{
	local cur prev words cword
	_init_completion || return
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-g --git -c --changelog -r --rpm --help' -- "$cur"))
	fi
}

_zephyr_lint()
{
	local cur prev words cword
	_init_completion || return
	case $prev in
		--color)
			COMPREPLY=($(compgen -W 'auto always never' -- "$cur"))
			return
			;;
	esac
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-v --verbose -q --quiet --strict --color --help' -- "$cur"))
	fi
}

complete -F _zephyr zephyr
complete -F _zephyr_create zephyr-create
complete -F _zephyr_rename zephyr-rename
complete -F _zephyr_add zephyr-add
complete -F _zephyr_remove zephyr-remove
complete -F _zephyr_about zephyr-about
complete -F _zephyr_version zephyr-version
complete -F _zephyr_lint zephyr-lint
