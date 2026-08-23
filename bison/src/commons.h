#ifndef COMMONS_H
#define COMMONS_H

#include <stdio.h>

typedef enum {
    COLOR_AUTO = 0,
    COLOR_ALWAYS,
    COLOR_NEVER,
} ColorMode;

typedef struct AstNode AstNode;

struct AstNode {
    int is_list;
    char *atom;
    AstNode **children;
    size_t nchildren;
};

AstNode *ast_atom(const char *text);
AstNode *ast_list(AstNode **children, size_t nchildren);
void ast_free(AstNode *node);

ColorMode parse_color_mode(const char *text);
int color_enabled(ColorMode mode, FILE *out);

void ast_dump(AstNode *node, FILE *out, ColorMode color, int indent);
void ast_format(AstNode *node, FILE *out, ColorMode color, int indent_size, int level);

#endif /* COMMONS_H */
