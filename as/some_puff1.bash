# bash completion for some_puff1

_some_puff1()
{
	local cur
	_init_completion || return
	_filedir
}

complete -F _some_puff1 some_puff1
