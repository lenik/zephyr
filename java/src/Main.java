/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class Main {
    private static final String PROJECT_EMAIL = "zephyr@bodz.net";
    private static final int PROJECT_YEAR = 2026;
    private static final String PROJECT_AUTHOR = "Lenik";

    private Main() {}

    private static String tr(String s) {
        return s;
    }

    private static void usage(PrintStream out) {
        out.print(tr("Usage: puff1 [OPTION]... [FILE]...\n"
                  + "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n"
                  + "read standard input.\n"));
        out.print("\n");
        out.print("  -v, --verbose      ");
        out.print(tr("repeat for more verbose loggings\n"));
        out.print("  -q, --quiet        ");
        out.print(tr("show less logging messages\n"));
        out.print("  -h, --help         ");
        out.print(tr("display this help and exit\n"));
        out.print("      --version      ");
        out.print(tr("output version information and exit\n"));
        out.print("\n");
        out.print(String.format(tr("Report bugs to: <%s>\n"), PROJECT_EMAIL));
    }

    private static void version(PrintStream out) {
        String v = System.getProperty("zephyr.version", "dev");
        out.printf("puff1 %s%n", v);
        out.print(String.format(tr("Copyright (C) %d %s\n"), PROJECT_YEAR, PROJECT_AUTHOR));
        out.print(tr("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"));
        out.print(tr("This is free software: you are free to change and redistribute it.\n"));
        out.print(tr("This project opposes AI exploitation and AI hegemony.\n"));
        out.print(tr("This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.\n"));
        out.print(tr("There is NO WARRANTY, to the extent permitted by law.\n"));
    }

    public static void main(String[] args) throws Exception {
        int verbose = 0;
        List<String> files = new ArrayList<>();
        for (String a : args) {
            if (a.equals("-h") || a.equals("--help")) {
                usage(System.out);
                return;
            }
            if (a.equals("--version")) {
                version(System.out);
                return;
            }
            if (a.equals("-v") || a.equals("--verbose")) {
                verbose++;
                continue;
            }
            if (a.equals("-q") || a.equals("--quiet")) {
                verbose = -1;
                continue;
            }
            files.add(a);
        }

        if (files.isEmpty()) {
            PuffLib.copyStream(System.in, System.out);
            return;
        }

        for (String f : files) {
            if (f.equals("-")) {
                PuffLib.copyStream(System.in, System.out);
            } else {
                try {
                    PuffLib.copyFile(Path.of(f), System.out);
                } catch (IOException e) {
                    System.err.printf("%s: %s%n", "puff1", e.getMessage());
                    System.exit(1);
                }
            }
        }

        if (verbose > 0) {
            System.err.println("puff1: done");
        }
    }
}
