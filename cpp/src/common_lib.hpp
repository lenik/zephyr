#ifndef COMMON_LIB_HPP
#define COMMON_LIB_HPP

#include <stdio.h>

int copy_stream(FILE *in, FILE *out);
int copy_file(const char *prog, const char *path);

#endif /* COMMON_LIB_HPP */
