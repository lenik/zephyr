// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

import commons;
import std.file;
import std.stdio;

void main() {
    import std.path : buildPath;
    import std.random : uniform;

    auto tmpIn = buildPath(tempDir, "some_puff1-in-" ~ uniform(1000, 9999).to!string);
    auto tmpOut = buildPath(tempDir, "some_puff1-out-" ~ uniform(1000, 9999).to!string);
    scope (exit) {
        if (exists(tmpIn))
            remove(tmpIn);
        if (exists(tmpOut))
            remove(tmpOut);
    }

    write(tmpIn, "alpha\nbeta\n");
    auto src = File(tmpIn, "rb");
    auto dst = File(tmpOut, "wb");
    copyStream(src, dst);
    src.close();
    dst.close();

    assert(readText(tmpOut) == "alpha\nbeta\n");
}
