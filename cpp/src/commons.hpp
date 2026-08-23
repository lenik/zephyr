#ifndef COMMONS_HPP
#define COMMONS_HPP

#include <stdio.h>

int copy_stream(FILE *in, FILE *out);
int copy_file(const char *prog, const char *path);

#endif /* COMMONS_HPP */
