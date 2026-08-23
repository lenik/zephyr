grammar SomePuff1;

program : sexpr EOF ;

sexpr
    : LPAREN RPAREN
    | LPAREN sexpr+ RPAREN
    | ATOM
    ;

LPAREN : '(' ;
RPAREN : ')' ;
ATOM   : ~[ \t\r\n()]+ ;
WS     : [ \t\r\n]+ -> skip ;
