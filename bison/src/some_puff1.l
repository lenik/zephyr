%{
/*
 * Copyright (C) 2026 Lenik <zephyr@bodz.net>
 *
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "commons.h"
#include "some_puff1.tab.h"
%}

%option noyywrap nounput noinput

%%

[ \t\r\n]+    ;
"("           { return '('; }
")"           { return ')'; }
[^ \t\r\n()]+ {
    yylval.str = strdup(yytext);
    return ATOM;
}

%%
