# bash completion for zfr and related wrappers
# SPDX-License-Identifier: AGPL-3.0-or-later

_zfr_langs='bash c clib cpp cpplib csharp erlang go haskell java perl python ruby rust smalltalk swift typescript'
_zfr_cmds='create rename add remove about version lint shape dist ize release detect help'

_zfr()
{
	local cur prev words cword
	_init_completion || return

	local cmd=
	local i
	for ((i = 1; i < cword; i++)); do
		case "${words[i]}" in
			create|rename|add|remove|about|version|lint|shape|dist|ize|release|detect|help)
				cmd="${words[i]}"
				break
				;;
		esac
	done

	if [[ -z $cmd ]]; then
		if [[ $cur == -* ]]; then
			COMPREPLY=($(compgen -W '--help --version' -- "$cur"))
		else
			COMPREPLY=($(compgen -W "$_zfr_cmds" -- "$cur"))
		fi
		return
	fi

	case $cmd in
		create)
			case $prev in
				-l|--lang)
					COMPREPLY=($(compgen -W "$_zfr_langs" -- "$cur"))
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
		shape)
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '-b --bool -v --verbose --threshold --help' -- "$cur"))
			fi
			;;
		dist)
			case $prev in
				-o|--output|-b|--builddir)
					_filedir -d
					return
					;;
				-f|--format)
					COMPREPLY=($(compgen -W 'xz gz zip' -- "$cur"))
					return
					;;
			esac
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '-o --output -b --builddir -f --format --rpm --allow-dirty --no-allow-dirty --tests --help' -- "$cur"))
			fi
			;;
		ize)
			case $prev in
				-l|--lang)
					COMPREPLY=($(compgen -W "$_zfr_langs" -- "$cur"))
					return
					;;
				--color)
					COMPREPLY=($(compgen -W 'auto always never' -- "$cur"))
					return
					;;
			esac
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '-l --lang -n --dry-run -v --verbose --no-man --no-subst --color --help' -- "$cur"))
			fi
			;;
		release)
			case $prev in
				-p|--dput-host|-B|--base-image|-s|--docker-server)
					COMPREPLY=()
					return
					;;
			esac
			if [[ $cur == -* ]]; then
				COMPREPLY=($(compgen -W '-b --build-binary -n --no-pre-clean -u --upload --unsigned -p --dput-host -d --docker -B --base-image -s --docker-server -l --local -f --force -I --no-install -T --no-tag -U --no-upload -R --no-release -P --no-publish -Y --no-rpm -D --no-deb -v --verbose -q --quiet --help' -- "$cur"))
			fi
			;;
		detect|help)
			COMPREPLY=()
			;;
	esac
}

_zfr_create()
{
	local cur prev words cword
	_init_completion || return

	case $prev in
		-l|--lang)
			COMPREPLY=($(compgen -W "$_zfr_langs" -- "$cur"))
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

_zfr_rename()
{
	local cur prev words cword
	_init_completion || return
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '--help' -- "$cur"))
		return
	fi
	_filedir
}

_zfr_add()
{
	_zfr_rename
}

_zfr_remove()
{
	_zfr_rename
}

_zfr_about()
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

_zfr_version()
{
	local cur prev words cword
	_init_completion || return
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-g --git -c --changelog -r --rpm --help' -- "$cur"))
	fi
}

_zfr_lint()
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

_zfr_dist()
{
	local cur prev words cword
	_init_completion || return
	case $prev in
		-o|--output|-b|--builddir)
			_filedir -d
			return
			;;
		-f|--format)
			COMPREPLY=($(compgen -W 'xz gz zip' -- "$cur"))
			return
			;;
	esac
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-o --output -b --builddir -f --format --rpm --allow-dirty --no-allow-dirty --tests --help' -- "$cur"))
	fi
}

complete -F _zfr zfr
complete -F _zfr_create zfr-create
complete -F _zfr_rename zfr-rename
complete -F _zfr_add zfr-add
complete -F _zfr_remove zfr-remove
complete -F _zfr_about zfr-about
complete -F _zfr_version zfr-version
complete -F _zfr_lint zfr-lint
complete -F _zfr_dist zfr-dist

_zfr_shape()
{
	local cur prev words cword
	_init_completion || return
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-b --bool -v --verbose --threshold --help' -- "$cur"))
	fi
}

complete -F _zfr_shape zfr-shape

_zfr_ize()
{
	local cur prev words cword
	_init_completion || return
	case $prev in
		-l|--lang)
			COMPREPLY=($(compgen -W "$_zfr_langs" -- "$cur"))
			return
			;;
		--color)
			COMPREPLY=($(compgen -W 'auto always never' -- "$cur"))
			return
			;;
	esac
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-l --lang -n --dry-run -v --verbose --no-man --no-subst --color --help' -- "$cur"))
	fi
}

complete -F _zfr_ize zfr-ize

_zfr_release()
{
	local cur prev words cword
	_init_completion || return
	case $prev in
		-p|--dput-host|-B|--base-image|-s|--docker-server)
			COMPREPLY=()
			return
			;;
	esac
	if [[ $cur == -* ]]; then
		COMPREPLY=($(compgen -W '-b --build-binary -n --no-pre-clean -u --upload --unsigned -p --dput-host -d --docker -B --base-image -s --docker-server -l --local -f --force -I --no-install -T --no-tag -U --no-upload -R --no-release -P --no-publish -Y --no-rpm -D --no-deb -v --verbose -q --quiet --help' -- "$cur"))
	fi
}

complete -F _zfr_release zfr-release
