grammar Lang;

// -----------------------------------------------------------------------------

// lexer rules

// symbols

ADDITION : '+' ;
SUBTRACTION : '-' ;
MULTIPLICATION : '*' ;
DIVISION : '/' ;
MODULO : '%' ;
POWER : '^' ;
EQUAL : '==' ;
UNEQUAL : '!=' ;
GEQ : '>=' ;
LEQ : '<=' ;
GREATER : '>' ;
LESSER : '<' ;
LPAREN : '(' ;
RPAREN : ')' ;
COMMA : ',' ;
SEMICOLON : ';' ;
ASSIGN : '=' ;
LBRACE : '{' ;
RBRACE : '}' ;

// keywords

TRUE : 'True' ;
FALSE : 'False' ;
AND : 'and';
OR : 'or';
NOT : 'not';
VAR : 'var' ;
CONST : 'const' ;
FLOAT : 'float' ;
BOOL : 'bool' ;
SKIPKW : 'skip' ;
PRINT : 'print' ;
IF : 'if' ;
ELSE : 'else' ;
WHILE : 'while' ;
RETURN : 'return' ;

// literal

FloatLit : (([0-9]+('.'[0-9]*)?)|('.'[0-9]+))([eE][+-]?[0-9]+)? ;

// user-defined

NamedValue : [_a-zA-Z] [_a-zA-Z0-9]* ;

// comments

Comment : '#' ~('\r'|'\n')* -> skip;

// whitespace

Whitespace : [ \t\r\n\f]+ -> skip;

// -----------------------------------------------------------------------------

// parser rules

typeQuantifier
  : CONST
  | VAR
  ;

dataType
  : FLOAT
  | BOOL
  ;

quantifiedType
  : typeQuantifier dataType
  ;

arithOp
  : ADDITION
  | SUBTRACTION
  | MULTIPLICATION
  | DIVISION
  | MODULO
  | POWER
  ;

compOp
  : EQUAL
  | UNEQUAL
  | GEQ
  | LEQ
  | GREATER
  | LESSER
  ;

binaryBoolOp
  : AND
  | OR
  ;

boolLit
  : TRUE
  | FALSE
  ;

expression
  : FloatLit # floatLiteralExp
  | boolLit # boolLiteralExp
  | NamedValue # namedValueExp
  | expression arithOp expression # arithExp
  | SUBTRACTION expression # minusExp
  | expression compOp expression # comparisonExp
  | expression binaryBoolOp expression # boolExp
  | NOT expression # notExp
  | LPAREN expression RPAREN # parenthesisExp
  | NamedValue LPAREN ( args+=expression ( COMMA args+=expression )* )? RPAREN # funcCallExp
  ;

statement
  : SKIPKW SEMICOLON # skipStmt
  | quantifiedType NamedValue ASSIGN expression SEMICOLON # valDeclStmt
  | funcRetType=dataType funcName=NamedValue LPAREN ( funcArgTypes+=quantifiedType funcArgNames+=NamedValue ( COMMA funcArgTypes+=quantifiedType funcArgNames+=NamedValue )* )? RPAREN LBRACE statement+ RBRACE # funcDeclStmt
  | NamedValue ASSIGN expression SEMICOLON # assignStmt
  | PRINT LPAREN expression RPAREN SEMICOLON # printStmt
  | IF expression LBRACE (ifBlock+=statement)+ RBRACE (ELSE LBRACE (elseBlock+=statement)+ RBRACE)? # ifElseStmt
  | WHILE expression LBRACE statement+ RBRACE # whileStmt
  | RETURN expression SEMICOLON # returnStmt
  ;

program
  : statement+
  ;

