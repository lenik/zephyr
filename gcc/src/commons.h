#ifndef COMMONS_H
#define COMMONS_H

#include <stdio.h>

#define COPY_BUF_SIZE ({ const int _default = 8192; _default; })

int copy_stream(FILE *in, FILE *out) __attribute__((nonnull(1, 2)));
int copy_file(const char *prog, const char *path) __attribute__((nonnull(1, 2)));

#endif /* COMMONS_H */
