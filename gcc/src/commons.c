/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

#define _GNU_SOURCE

#include "commons.h"

#include <stdio.h>

int copy_stream(FILE *in, FILE *out) {
    char buf[COPY_BUF_SIZE];
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
