-module(common_lib).
-export([copy_file/1, copy_stream/2]).

copy_stream(In, Out) ->
    case file:read(In, 65536) of
        eof ->
            ok;
        {ok, Bin} ->
            ok = file:write(Out, Bin),
            copy_stream(In, Out);
        {error, Reason} ->
            {error, Reason}
    end.

copy_file(Path) ->
    case file:open(Path, [read, binary]) of
        {ok, In} ->
            Result = copy_stream(In, standard_io),
            ok = file:close(In),
            Result;
        {error, Reason} ->
            {error, Reason}
    end.
