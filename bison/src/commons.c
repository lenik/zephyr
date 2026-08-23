/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

#define _POSIX_C_SOURCE 200809L

#include "commons.h"

#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define C_RESET "\033[0m"
#define C_LPAREN "\033[36m"
#define C_RPAREN "\033[36m"
#define C_ATOM "\033[33m"
#define C_LABEL "\033[35m"

AstNode *ast_atom(const char *text) {
    AstNode *node = calloc(1, sizeof *node);
    if (!node) {
        return NULL;
    }
    node->is_list = 0;
    node->atom = strdup(text ? text : "");
    return node;
}

AstNode *ast_list(AstNode **children, size_t nchildren) {
    AstNode *node = calloc(1, sizeof *node);
    if (!node) {
        return NULL;
    }
    node->is_list = 1;
    if (nchildren > 0) {
        node->children = calloc(nchildren, sizeof *node->children);
        if (!node->children) {
            free(node);
            return NULL;
        }
        memcpy(node->children, children, nchildren * sizeof *children);
        node->nchildren = nchildren;
    }
    return node;
}

void ast_free(AstNode *node) {
    size_t i;

    if (!node) {
        return;
    }
    if (node->is_list) {
        for (i = 0; i < node->nchildren; i++) {
            ast_free(node->children[i]);
        }
        free(node->children);
    } else {
        free(node->atom);
    }
    free(node);
}

ColorMode parse_color_mode(const char *text) {
    if (!text || !*text || strcmp(text, "auto") == 0) {
        return COLOR_AUTO;
    }
    if (strcmp(text, "always") == 0) {
        return COLOR_ALWAYS;
    }
    return COLOR_NEVER;
}

int color_enabled(ColorMode mode, FILE *out) {
    if (mode == COLOR_NEVER) {
        return 0;
    }
    if (mode == COLOR_ALWAYS) {
        return 1;
    }
    return isatty(fileno(out));
}

static void print_atom(FILE *out, ColorMode color, const char *label, const char *text) {
    if (color_enabled(color, out)) {
        fprintf(out, "%s%s%s \"%s\"", C_LABEL, label, C_RESET, text);
    } else {
        fprintf(out, "%s \"%s\"", label, text);
    }
}

static void print_paren(FILE *out, ColorMode color, char paren) {
    if (color_enabled(color, out)) {
        fprintf(out, "%c%s", paren, C_RESET);
    } else {
        fputc(paren, out);
    }
}

void ast_dump(AstNode *node, FILE *out, ColorMode color, int indent) {
    size_t i;

    if (!node) {
        return;
    }
    for (i = 0; i < (size_t)indent; i++) {
        fputs("  ", out);
    }
    if (node->is_list) {
        if (color_enabled(color, out)) {
            fprintf(out, "%slist%s (%zu)\n", C_LABEL, C_RESET, node->nchildren);
        } else {
            fprintf(out, "list (%zu)\n", node->nchildren);
        }
        for (i = 0; i < node->nchildren; i++) {
            ast_dump(node->children[i], out, color, indent + 1);
        }
    } else {
        print_atom(out, color, "atom", node->atom ? node->atom : "");
        fputc('\n', out);
    }
}

void ast_format(AstNode *node, FILE *out, ColorMode color, int indent_size, int level) {
    size_t i;

    if (!node) {
        return;
    }
    if (!node->is_list) {
        if (color_enabled(color, out)) {
            fprintf(out, "%s%s%s", C_ATOM, node->atom ? node->atom : "", C_RESET);
        } else {
            fputs(node->atom ? node->atom : "", out);
        }
        return;
    }

    print_paren(out, color, '(');
    if (node->nchildren == 0) {
        print_paren(out, color, ')');
        return;
    }

    for (i = 0; i < node->nchildren; i++) {
        if (i > 0) {
            fputc('\n', out);
            for (size_t s = 0; s < (size_t)(level + 1) * (size_t)indent_size; s++) {
                fputc(' ', out);
            }
        } else if (node->nchildren == 1) {
            fputc(' ', out);
        }
        ast_format(node->children[i], out, color, indent_size, level + 1);
    }

    if (node->nchildren == 1) {
        fputc(' ', out);
    }
    print_paren(out, color, ')');
}
