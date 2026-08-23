/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

#define _GNU_SOURCE

#include "commons.h"
#include "config.h"

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { OPT_VERSION = 256 };

__attribute__((unused)) static int verbose;

static int max_int(int a, int b) {
    return ({ typeof(a) _a = (a); typeof(b) _b = (b); _a > _b ? _a : _b; });
}

static void usage(FILE *out) {
    fputs("Usage: some_puff1 [OPTION]... [FILE]...\n"
          "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n"
          "read standard input.\n\n"
          "  -v, --verbose      repeat for more verbose loggings\n"
          "  -q, --quiet        show less logging messages\n"
          "  -h, --help         display this help and exit\n"
          "      --version      output version information and exit\n\n",
          out);
    fprintf(out, "Report bugs to: <%s>\n", PROJECT_EMAIL);
}

int main(int argc, char **argv) {
    const char *prog = argv[0] ? argv[0] : "some_puff1";

    static const struct option long_opts[] = {
        {"verbose", no_argument, NULL, 'v'},
        {"quiet", no_argument, NULL, 'q'},
        {"help", no_argument, NULL, 'h'},
        {"version", no_argument, NULL, OPT_VERSION},
        {NULL, 0, NULL, 0},
    };

    for (;;) {
        int c = getopt_long(argc, argv, "vqh", long_opts, NULL);
        if (c == -1) {
            break;
        }
        switch (c) {
        case 'v':
            verbose = max_int(verbose + 1, 0);
            break;
        case 'q':
            verbose = -1;
            break;
        case 'h':
            usage(stdout);
            return 0;
        case OPT_VERSION:
            printf("some_puff1 %s\n", PROJECT_VERSION);
            printf("Copyright (C) %d %s\n", PROJECT_YEAR, PROJECT_AUTHOR);
            fputs("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"
                  "This is free software: you are free to change and redistribute it.\n"
                  "There is NO WARRANTY, to the extent permitted by law.\n",
                  stdout);
            return 0;
        default:
            usage(stderr);
            return 1;
        }
    }

    argc -= optind;
    argv += optind;

    if (verbose > 0) {
        fprintf(stderr, "%s: verbose mode enabled\n", prog);
    }

    if (argc == 0) {
        return copy_stream(stdin, stdout) == 0 ? 0 : 1;
    }

    for (int i = 0; i < argc; i++) {
        const char *path = argv[i];
        if (strcmp(path, "-") == 0) {
            if (copy_stream(stdin, stdout) != 0) {
                return 1;
            }
        } else if (copy_file(prog, path) != 0) {
            return 1;
        }
    }

    return 0;
}
