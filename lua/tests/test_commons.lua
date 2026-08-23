-- Copyright (C) 2026 Lenik <zephyr@bodz.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

package.path = (os.getenv("LUA_PATH") or "") .. ";" .. "../src/?.lua"
local commons = require("commons")

local function assert_eq(got, want, msg)
    if got ~= want then
        error(string.format("%s: got %q want %q", msg or "assert_eq", got, want))
    end
end

local function test_copy_stream_roundtrip()
    local src = io.tmpfile()
    local dst = io.tmpfile()
    src:write("alpha\nbeta\n")
    src:seek("set", 0)
    commons.copy_stream(src, dst)
    dst:seek("set", 0)
    assert_eq(dst:read("*a"), "alpha\nbeta\n", "copy_stream roundtrip")
end

local ok, err = pcall(test_copy_stream_roundtrip)
if not ok then
    io.stderr:write("FAIL: " .. tostring(err) .. "\n")
    os.exit(1)
end
print("ok")
