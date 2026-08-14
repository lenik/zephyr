#ifndef LIB_HPP
#define LIB_HPP

#include <stdio.h>

int copy_stream(FILE *in, FILE *out);
int copy_file(const char *prog, const char *path);

#endif /* LIB_HPP */