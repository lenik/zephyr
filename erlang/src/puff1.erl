-module(puff1).
-export([main/0]).

tr(S) -> S.

usage() ->
    io:put_chars(tr("Usage: puff1 [OPTION]... [FILE]...\n")),
    io:put_chars(tr("Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n")),
    io:put_chars(tr("read standard input.\n\n")),
    io:put_chars("  -v, --verbose      "),
    io:put_chars(tr("repeat for more verbose loggings\n")),
    io:put_chars("  -q, --quiet        "),
    io:put_chars(tr("show less logging messages\n")),
    io:put_chars("  -h, --help         "),
    io:put_chars(tr("display this help and exit\n")),
    io:put_chars("      --version      "),
    io:put_chars(tr("output version information and exit\n\n")),
    io:format(tr("Report bugs to: <~s>~n"), ["zephyr@bodz.net"]).

version_info() ->
    io:put_chars("puff1 dev\n"),
    io:put_chars(tr("Copyright (C) 2026 Lenik\n")),
    io:put_chars(tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n")),
    io:put_chars(tr("This is free software: you are free to change and redistribute it.\n")),
    io:put_chars(tr("This project opposes AI exploitation and AI hegemony.\n")),
    io:put_chars(tr("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.\n")),
    io:put_chars(tr("There is NO WARRANTY, to the extent permitted by law.\n")).

copy_files([]) ->
    ok;
copy_files(["-" | Rest]) ->
    case common_lib:copy_stream(standard_io, standard_io) of
        ok -> copy_files(Rest);
        {error, Reason} -> {error, Reason}
    end;
copy_files([File | Rest]) ->
    case common_lib:copy_file(File) of
        ok -> copy_files(Rest);
        {error, Reason} -> {error, {File, Reason}}
    end.

main() ->
    Args = init:get_plain_arguments(),
    case lists:member("-h", Args) orelse lists:member("--help", Args) of
        true ->
            usage(),
            erlang:halt(0);
        false ->
            ok
    end,
    case lists:member("--version", Args) of
        true ->
            version_info(),
            erlang:halt(0);
        false ->
            ok
    end,
    Verbose = lists:member("-v", Args) orelse lists:member("--verbose", Args),
    Files = [A || A <- Args, not lists:member(A, ["-v", "--verbose", "-q", "--quiet"])],
    case Verbose of
        true -> io:format(standard_error, "~s: verbose mode enabled~n", ["puff1"]);
        false -> ok
    end,
    case Files of
        [] ->
            _ = common_lib:copy_stream(standard_io, standard_io),
            erlang:halt(0);
        _ ->
            case copy_files(Files) of
                ok ->
                    erlang:halt(0);
                {error, {File, Reason}} ->
                    io:format(standard_error, "puff1: ~s: ~p~n", [File, Reason]),
                    erlang:halt(1);
                {error, Reason} ->
                    io:format(standard_error, "puff1: ~p~n", [Reason]),
                    erlang:halt(1)
            end
    end.
