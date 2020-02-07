grammar Lang;

// -----------------------------------------------------------------------------

// lexer rules

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

FloatLit : [+-]?(([0-9]+('.'[0-9]*)?)|('.'[0-9]+))([eE][+-]?[0-9]+)? ;

// user-defined

NamedValue : [_a-zA-Z] [_a-zA-Z0-9]* ;

// comments

Comment : '#' ~('\r'|'\n')* -> channel(HIDDEN);

// whitespace

Whitespace : [ \t\r\n\f]+ -> channel(HIDDEN);

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
  : '+'
  | '-'
  | '*'
  | '/'
  | '%'
  | '^'
  ;

compOp
  : '=='
  | '!='
  | '>'
  | '<'
  | '>='
  | '<='
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
  | expression compOp expression # comparisonExp
  | expression binaryBoolOp expression # boolExp
  | NOT expression # negationExp
  | '(' expression ')' # parenthesisExp
  | NamedValue '(' ( expression ( ',' expression )* )? ')' # funcCallExp
  ;

statement
  : SKIPKW ';' # skipStmt
  | quantifiedType NamedValue '=' expression ';' # valDeclStmt
  | dataType NamedValue '(' ( quantifiedType NamedValue ( ',' quantifiedType NamedValue )* )? ')' '{' statement+ '}' # funcDeclStmt
  | NamedValue '=' expression ';' # assignStmt
  | PRINT '(' expression ')' ';' # printStmt
  | IF expression '{' (ifBlock+=statement)+ '}' (ELSE '{' (elseBlock+=statement)+ '}')? # ifElseStmt
  | WHILE expression '{' statement+ '}' # whileStmt
  | RETURN expression ';' # returnStmt
  ;

program
  : statement+
  ;

