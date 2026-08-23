#!/usr/bin/env lua
-- Copyright (C) 2026 Lenik <zephyr@bodz.net>
-- SPDX-License-Identifier: AGPL-3.0-or-later

local sep = package.config:sub(1, 1)
local script_dir = arg[0]:match("(.*" .. sep .. ")") or ("." .. sep)
package.path = script_dir .. "?.lua;" .. package.path

local commons = require("commons")

local PROJECT_EMAIL = "zephyr@bodz.net"
local PROJECT_YEAR = 2026
local PROJECT_AUTHOR = "Lenik"

local function tr(s)
    return s
end

local function usage(out)
    out:write(tr("Usage: some_puff1 [OPTION]... [FILE]...\n"))
    out:write(tr("Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n"))
    out:write(tr("read standard input.\n"))
    out:write("\n")
    out:write("  -v, --verbose      ")
    out:write(tr("repeat for more verbose loggings\n"))
    out:write("  -q, --quiet        ")
    out:write(tr("show less logging messages\n"))
    out:write("  -h, --help         ")
    out:write(tr("display this help and exit\n"))
    out:write("      --version      ")
    out:write(tr("output version information and exit\n"))
    out:write("\n")
    out:write(string.format(tr("Report bugs to: <%s>\n"), PROJECT_EMAIL))
end

local function version(out)
    out:write("some_puff1 dev\n")
    out:write(string.format(tr("Copyright (C) %d %s\n"), PROJECT_YEAR, PROJECT_AUTHOR))
    out:write(tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"))
    out:write(tr("This is free software: you are free to change and redistribute it.\n"))
    out:write(tr("This project opposes AI exploitation and AI hegemony.\n"))
    out:write(tr("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.\n"))
    out:write(tr("There is NO WARRANTY, to the extent permitted by law.\n"))
end

local function main(argv)
    local args = {}
    for i = 2, #argv do
        args[#args + 1] = argv[i]
    end

    local verbose = 0
    local files = {}
    local i = 1
    while i <= #args do
        local a = args[i]
        if a == "-h" or a == "--help" then
            usage(io.stdout)
            return 0
        end
        if a == "--version" then
            version(io.stdout)
            return 0
        end
        if a == "-v" or a == "--verbose" then
            verbose = verbose + 1
            i = i + 1
        elseif a == "-q" or a == "--quiet" then
            verbose = -1
            i = i + 1
        else
            files[#files + 1] = a
            i = i + 1
        end
    end

    if verbose > 0 then
        io.stderr:write(string.format("%s: verbose mode enabled\n", argv[1] or "some_puff1"))
    end

    local out = io.stdout
    if #files == 0 then
        commons.copy_stream(io.stdin, out)
        return 0
    end

    for _, path in ipairs(files) do
        if path == "-" then
            commons.copy_stream(io.stdin, out)
        else
            local ok, err = pcall(function()
                commons.copy_file(path, out)
            end)
            if not ok then
                io.stderr:write(string.format("%s: %s\n", argv[1] or "some_puff1", tostring(err)))
                return 1
            end
        end
    end
    return 0
end

os.exit(main(arg))
