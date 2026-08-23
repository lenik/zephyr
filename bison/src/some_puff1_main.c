/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

#define _POSIX_C_SOURCE 200809L

#include "commons.h"
#include "config.h"

#include <errno.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern AstNode *parse_result;
extern FILE *yyin;
int yyparse(void);

enum { OPT_VERSION = 256, OPT_INDENT = 257 };

static int process_file(
    const char *prog,
    const char *path,
    int dump,
    ColorMode color,
    int indent_size
) {
    FILE *in = stdin;
    int rc = 0;

    if (path && strcmp(path, "-") != 0) {
        in = fopen(path, "rb");
        if (!in) {
            fprintf(stderr, "%s: ", prog);
            perror(path);
            return 1;
        }
    }

    yyin = in;
    parse_result = NULL;
    if (yyparse() != 0 || !parse_result) {
        fprintf(stderr, "%s: failed to parse %s\n", prog, path ? path : "stdin");
        rc = 1;
    } else if (dump) {
        ast_dump(parse_result, stdout, color, 0);
    } else {
        ast_format(parse_result, stdout, color, indent_size, 0);
        fputc('\n', stdout);
    }

    ast_free(parse_result);
    parse_result = NULL;

    if (in != stdin) {
        fclose(in);
    }
    return rc;
}

static void usage(FILE *out) {
    fputs(
        "Usage: some_puff1 [OPTION]... [FILE]...\n"
        "Parse simple s-expressions and dump or format the AST.\n"
        "With no FILE, or when FILE is -, read standard input.\n\n"
        "  -d, --dump           AST dump\n"
        "  -f, --format         format rewrite (default)\n"
        "      --indent-size NUM  indentation width (default 4)\n"
        "  -C, --color MODE     auto|always|never (default auto)\n"
        "  -h, --help           display this help and exit\n"
        "      --version        output version information and exit\n\n",
        out
    );
    fprintf(out, "Report bugs to: <%s>\n", PROJECT_EMAIL);
}

int main(int argc, char **argv) {
    const char *prog = argv[0] ? argv[0] : "some_puff1";
    int dump = 0;
    int format = 0;
    int indent_size = 4;
    ColorMode color = COLOR_AUTO;
    int rc = 0;
    int i;

    static const struct option long_opts[] = {
        {"dump", no_argument, NULL, 'd'},
        {"format", no_argument, NULL, 'f'},
        {"indent-size", required_argument, NULL, OPT_INDENT},
        {"color", required_argument, NULL, 'C'},
        {"help", no_argument, NULL, 'h'},
        {"version", no_argument, NULL, OPT_VERSION},
        {NULL, 0, NULL, 0},
    };

    for (;;) {
        int c = getopt_long(argc, argv, "dfC:h", long_opts, NULL);
        if (c == -1) {
            break;
        }
        switch (c) {
        case 'd':
            dump = 1;
            break;
        case 'f':
            format = 1;
            break;
        case OPT_INDENT:
            indent_size = atoi(optarg);
            if (indent_size < 0) {
                indent_size = 0;
            }
            break;
        case 'C':
            color = parse_color_mode(optarg);
            break;
        case 'h':
            usage(stdout);
            return 0;
        case OPT_VERSION:
            printf("some_puff1 %s\n", PROJECT_VERSION);
            printf("Copyright (C) %d %s\n", PROJECT_YEAR, PROJECT_AUTHOR);
            fputs(
                "License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"
                "This is free software: you are free to change and redistribute it.\n"
                "There is NO WARRANTY, to the extent permitted by law.\n",
                stdout
            );
            return 0;
        default:
            usage(stderr);
            return 1;
        }
    }

    (void)format;
    if (!dump) {
        dump = 0;
    }

    argc -= optind;
    argv += optind;

    if (argc == 0) {
        return process_file(prog, NULL, dump, color, indent_size);
    }

    for (i = 0; i < argc; i++) {
        rc |= process_file(prog, argv[i], dump, color, indent_size);
    }
    return rc != 0;
}
