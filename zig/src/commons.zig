//! Copyright (C) 2026 Lenik <zephyr@bodz.net>
//! SPDX-License-Identifier: AGPL-3.0-or-later
//!
//! Template example: shared helpers live in src/commons.* (not a real module name).

const std = @import("std");

pub fn copyStream(reader: anytype, writer: anytype) !void {
    var buf: [8192]u8 = undefined;
    while (true) {
        const n = try reader.read(&buf);
        if (n == 0) return;
        try writer.writeAll(buf[0..n]);
    }
}

pub fn copyFileToStdout(path: []const u8) !void {
    const file = try std.fs.cwd().openFile(path, .{});
    defer file.close();
    const stdout = std.io.getStdOut().writer();
    try copyStream(file.reader(), stdout);
}

test "copyStream roundtrip" {
    const input = "alpha\nbeta\n";
    var in = std.io.fixedBufferStream(input);
    var out: std.ArrayList(u8) = .empty;
    defer out.deinit(std.testing.allocator);
    try copyStream(in.reader(), out.writer(std.testing.allocator));
    try std.testing.expectEqualStrings(input, out.items);
}
