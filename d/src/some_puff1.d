// Copyright (C) 2026 Lenik <zephyr@bodz.net>
// SPDX-License-Identifier: AGPL-3.0-or-later

import commons;
import std.stdio;
import std.file;

string tr(string s) {
    return s;
}

void usage() {
    writeln(tr("Usage: some_puff1 [OPTION]... [FILE]..."));
    writeln(tr("Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,"));
    writeln(tr("read standard input.\n"));
    writeln("  -v, --verbose      ", tr("repeat for more verbose loggings"));
    writeln("  -q, --quiet        ", tr("show less logging messages"));
    writeln("  -h, --help         ", tr("display this help and exit"));
    writeln("      --version      ", tr("output version information and exit\n"));
    writeln(tr("Report bugs to: <zephyr@bodz.net>"));
}

void showVersion() {
    writeln("some_puff1 dev");
    writeln(tr("Copyright (C) 2026 Lenik"));
    writeln(tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>"));
}

int main(string[] args) {
    if (args.length > 1 && (args[1] == "-h" || args[1] == "--help")) {
        usage();
        return 0;
    }
    if (args.length > 1 && args[1] == "--version") {
        showVersion();
        return 0;
    }

    int verbose = 0;
    string[] files;
    foreach (a; args[1 .. $]) {
        if (a == "-v" || a == "--verbose")
            verbose++;
        else if (a == "-q" || a == "--quiet")
            verbose = -1;
        else
            files ~= a;
    }

    if (verbose > 0)
        stderr.writeln("some_puff1: verbose mode enabled");

    if (files.length == 0) {
        if (verbose > 0)
            stderr.writeln("some_puff1: reading from standard input");
        copyStream(stdin, stdout);
        return 0;
    }

    foreach (path; files) {
        if (path == "-") {
            if (verbose > 0)
                stderr.writeln("some_puff1: copying from standard input");
            copyStream(stdin, stdout);
        } else {
            if (verbose > 0)
                stderr.writeln("some_puff1: copying from ", path);
            copyFile(path, stdout);
        }
    }
    return 0;
}
