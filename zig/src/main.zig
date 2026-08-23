//! Copyright (C) 2026 Lenik <zephyr@bodz.net>
//! SPDX-License-Identifier: AGPL-3.0-or-later

const std = @import("std");
const commons = @import("commons.zig");

const project_email = "zephyr@bodz.net";
const project_year: u16 = 2026;
const project_author = "Lenik";

fn tr(comptime s: []const u8) []const u8 {
    return s;
}

fn usage(out: anytype) !void {
    try out.writeAll(tr(
        \\Usage: some_puff1 [OPTION]... [FILE]...
        \\Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,
        \\read standard input.
        \\
    ));
    try out.writeAll("  -v, --verbose      ");
    try out.writeAll(tr("repeat for more verbose loggings\n"));
    try out.writeAll("  -q, --quiet        ");
    try out.writeAll(tr("show less logging messages\n"));
    try out.writeAll("  -h, --help         ");
    try out.writeAll(tr("display this help and exit\n"));
    try out.writeAll("      --version      ");
    try out.writeAll(tr("output version information and exit\n"));
    try out.writeAll("\n");
    try out.print(tr("Report bugs to: <{s}>\n"), .{project_email});
}

fn version(out: anytype) !void {
    try out.writeAll("some_puff1 dev\n");
    try out.print(tr("Copyright (C) {d} {s}\n"), .{ project_year, project_author });
    try out.writeAll(tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"));
    try out.writeAll(tr("This is free software: you are free to change and redistribute it.\n"));
    try out.writeAll(tr("This project opposes AI exploitation and AI hegemony.\n"));
    try out.writeAll(tr("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.\n"));
    try out.writeAll(tr("There is NO WARRANTY, to the extent permitted by law.\n"));
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var args = try std.process.argsWithAllocator(allocator);
    defer args.deinit();

    _ = args.next();

    var verbose: i32 = 0;
    var files = std.ArrayList([]const u8).empty;
    defer files.deinit(allocator);

    while (args.next()) |arg| {
        if (std.mem.eql(u8, arg, "-h") or std.mem.eql(u8, arg, "--help")) {
            try usage(std.io.getStdOut().writer());
            return;
        }
        if (std.mem.eql(u8, arg, "--version")) {
            try version(std.io.getStdOut().writer());
            return;
        }
        if (std.mem.eql(u8, arg, "-v") or std.mem.eql(u8, arg, "--verbose")) {
            verbose += 1;
            continue;
        }
        if (std.mem.eql(u8, arg, "-q") or std.mem.eql(u8, arg, "--quiet")) {
            verbose = -1;
            continue;
        }
        try files.append(allocator, arg);
    }

    if (verbose > 0) {
        try std.io.getStdErr().writer().writeAll("some_puff1: verbose mode enabled\n");
    }

    const stdout = std.io.getStdOut().writer();
    if (files.items.len == 0) {
        try commons.copyStream(std.io.getStdIn().reader(), stdout);
        return;
    }

    for (files.items) |path| {
        if (std.mem.eql(u8, path, "-")) {
            try commons.copyStream(std.io.getStdIn().reader(), stdout);
        } else {
            commons.copyFileToStdout(path) catch |err| {
                try std.io.getStdErr().writer().print("some_puff1: {s}\n", .{@errorName(err)});
                std.process.exit(1);
            };
        }
    }
}
