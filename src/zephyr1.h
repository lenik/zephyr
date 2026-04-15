#ifndef ZEPHYR1_H
#define ZEPHYR1_H

#include <stdio.h>

int copy_stream(FILE *in, FILE *out);
int copy_file(const char *prog, const char *path);
void usage(FILE *out);

#endif
