%{
/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

#include <stdio.h>
#include <stdlib.h>

#include "commons.h"

extern int yylex(void);
extern FILE *yyin;

AstNode *parse_result;

void yyerror(const char *msg) {
    fprintf(stderr, "parse error: %s\n", msg);
}
%}

%union {
    char *str;
    AstNode *node;
}

%token <str> ATOM
%type <node> sexpr sexpr_list

%%

program
    : sexpr { parse_result = $1; }
    ;

sexpr
    : '(' ')' { $$ = ast_list(NULL, 0); }
    | '(' sexpr_list ')' { $$ = $2; }
    | ATOM {
        $$ = ast_atom($1);
        free($1);
      }
    ;

sexpr_list
    : sexpr { $$ = ast_list(&$1, 1); }
    | sexpr_list sexpr {
        AstNode *list = $1;
        size_t n = list->nchildren + 1;
        AstNode **items = realloc(list->children, n * sizeof *items);
        if (!items) {
            YYERROR;
        }
        list->children = items;
        list->children[list->nchildren++] = $2;
        $$ = list;
      }
    ;

%%
