/*
 * Copyright (C) 2026 Lenik <ZEPHYR@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

#define _POSIX_C_SOURCE 200809L

#include "zephyr1.h"
#include "config.h"

#include <bas/log/deflog.h>

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
define_logger();

enum { OPT_VERSION = 256 };

int copy_stream(FILE *in, FILE *out) {
    char buf[8192];
    size_t n;

    while ((n = fread(buf, 1, sizeof buf, in)) > 0) {
        if (fwrite(buf, 1, n, out) != n) {
            return -1;
        }
    }
    if (ferror(in)) {
        return -1;
    }
    return 0;
}

int copy_file(const char *prog, const char *path) {
    loginfo_fmt("%s: copying from %s", prog, path);

    FILE *f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "%s: ", prog);
        perror(path);
        return -1;
    }

    int r = copy_stream(f, stdout);
    if (fclose(f) != 0) {
        r = -1;
    }
    if (r != 0) {
        fprintf(stderr, "%s: write error\n", prog);
        return -1;
    }
    return 0;
}

void usage(FILE *out) {
    fprintf(out,
            "Usage: zephyr1 [OPTION]... [FILE]...\n"
            "Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n"
            "read standard input.\n"
            "\n"
            "  -v, --verbose   print each file name to standard error before copying\n"
            "  -q, --quiet     suppress --verbose messages\n"
            "  -h, --help      display this help and exit\n"
            "      --version   output version information and exit\n"
            "\n"
            "Report bugs to: <%s>\n",
            PROJECT_EMAIL);
}

#ifndef ZEPHYR1_NO_MAIN
int main(int argc, char **argv) {
    const char *prog = argv[0];
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
            log_more();
            break;
        case 'q':
            log_less();
            break;
        case 'h':
            usage(stdout);
            return 0;
        case OPT_VERSION:
            printf("%s %s\n"
                   "Copyright (C) %d %s\n"
                   "License AGPL-3.0-or-later: "
                   "<https://www.gnu.org/licenses/agpl-3.0.html>\n"
                   "This is free software: you are free to change and redistribute it.\n"
                   "There is NO WARRANTY, to the extent permitted by law.\n",
                   PROJECT_NAME, PROJECT_VERSION, PROJECT_YEAR, PROJECT_AUTHOR);
            return 0;
        default:
            usage(stderr);
            return 1;
        }
    }

    argc -= optind;
    argv += optind;

    loginfo_fmt("%s: verbose mode enabled", prog);

    if (argc == 0) {
        loginfo_fmt("%s: reading from standard input", prog);
        if (copy_stream(stdin, stdout) != 0) {
            fprintf(stderr, "%s: ", prog);
            perror("stdin");
            return 1;
        }
        loginfo_fmt("%s: done", prog);
        return 0;
    }

    for (int i = 0; i < argc; i++) {
        const char *path = argv[i];
        if (strcmp(path, "-") == 0) {
            loginfo_fmt("%s: copying from standard input", prog);
            if (copy_stream(stdin, stdout) != 0) {
                fprintf(stderr, "%s: ", prog);
                perror("stdin");
                return 1;
            }
        } else if (copy_file(prog, path) != 0) {
            return 1;
        } else {
            loginfo_fmt("%s: copied %s", prog, path);
        }
    }
    loginfo_fmt("%s: done", prog);

    return 0;
}
#endif
