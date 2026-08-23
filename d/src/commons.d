// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

module commons;

import std.stdio;

void copyStream(File src, File dst) {
    ubyte[8192] buf;
    while (!src.eof) {
        auto n = src.rawRead(buf);
        if (n.length == 0)
            break;
        dst.rawWrite(n);
        dst.flush();
    }
}

void copyFile(string path, File dst) {
    auto src = File(path, "rb");
    scope (exit)
        src.close();
    copyStream(src, dst);
}
