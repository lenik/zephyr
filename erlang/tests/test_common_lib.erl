-module(test_common_lib).
-export([run/0]).

run() ->
    In = <<"alpha\nbeta\n">>,
    Tmp = filename:join("/tmp", "common_lib-test-input.txt"),
    ok = file:write_file(Tmp, In),
    {ok, Bin} = file:read_file(Tmp),
    true = (Bin =:= In),
    ok = file:delete(Tmp),
    ok.
