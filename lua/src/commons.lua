-- Copyright (C) 2026 Lenik <zephyr@bodz.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later
--
-- Template example: shared helpers live in src/commons.* (not a real module name).
-- In a concrete program, rename to something specific (e.g. stream_copy.lua).

local commons = {}

function commons.copy_stream(src, dst)
    while true do
        local chunk = src:read(8192)
        if not chunk then
            return
        end
        dst:write(chunk)
        dst:flush()
    end
end

function commons.copy_file(path, out)
    local fh, err = io.open(path, "rb")
    if not fh then
        error(err, 0)
    end
    local ok, copy_err = pcall(function()
        commons.copy_stream(fh, out)
    end)
    fh:close()
    if not ok then
        error(copy_err, 0)
    end
end

return commons
