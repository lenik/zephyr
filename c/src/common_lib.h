#ifndef COMMON_LIB_H
#define COMMON_LIB_H

#include <stdio.h>

int copy_stream(FILE *in, FILE *out);
int copy_file(const char *prog, const char *path);

#endif /* COMMON_LIB_H */
