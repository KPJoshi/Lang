#! /usr/bin/env python3

from enum import Enum
import sys
from antlr4 import CommonTokenStream, InputStream
from LangLexer import LangLexer
from LangParser import LangParser
from LangVisitor import LangVisitor

# type quantifiers
class TypeQuantifier(Enum):
  Const = 1
  Var = 2

  def parse(str):
    if str=='const':
      return TypeQuantifier.Const
    elif str=='var':
      return TypeQuantifier.Var

# data types
class DataType(Enum):
  Float = 1
  Bool = 2

  def parse(str):
    if str=='float':
      return DataType.Float
    elif str=='bool':
      return DataType.Bool

# stores variable quantifier, type, and value
class VariableRecord:
  def __init__(self, typeQuantifier, dataType, value):
    self.typeQuantifier = typeQuantifier
    self.dataType = dataType
    self.value = value

# stores function return type, arguments, and body
class FunctionRecord:
  def __init__(self, dataType, params, body):
    self.dataType = dataType
    self.params = params
    self.body = body

class FunctionReturnedException(Exception):
    pass

# interprets the language
class LangInterpreter(LangVisitor):

  def __init__(self):
    self.environment = None

  # search for name in environment, starting from innermost scope
  def getRecordFromName(self, name):
    for scope in self.environment[::-1]:
      if name in scope:
        return scope[name]
    raise Exception('Undefined name {}'.format(name))

  def visitFloatLiteralExp(self, ctx):
    return VariableRecord(TypeQuantifier.Const, DataType.Float, float(ctx.getText()))

  def visitBoolLiteralExp(self, ctx):
    return VariableRecord(TypeQuantifier.Const, DataType.Bool, ctx.getText()=='True')

  def visitNamedValueExp(self, ctx):
    name = ctx.NamedValue().getText()
    return self.getRecordFromName(name)

  def visitArithExp(self, ctx):
    value0 = self.visit(ctx.expression(0))
    value1 = self.visit(ctx.expression(1))
    assert(value0.dataType == value1.dataType and value0.dataType == DataType.Float)
    op = ctx.arithOp().getText()
    resultValue = 0.0
    if op == '+':
      resultValue = value0.value + value1.value
    elif op == '-':
      resultValue = value0.value - value1.value
    elif op == '*':
      resultValue = value0.value * value1.value
    elif op == '/':
      resultValue = value0.value / value1.value
    elif op == '%':
      resultValue = value0.value % value1.value
    elif op == '^':
      resultValue = value0.value ** value1.value
    else:
      raise Exception('Invalid arithmetic operand ({})'.format(op))
    return VariableRecord(TypeQuantifier.Const, DataType.Float, resultValue)

  def visitComparisonExp(self, ctx):
    value0 = self.visit(ctx.expression(0))
    value1 = self.visit(ctx.expression(1))
    assert(value0.dataType == value1.dataType)
    op = ctx.compOp().getText()
    resultValue = None
    if op == '==':
      resultValue = ( value0.value == value1.value )
    elif op == '!=':
      resultValue = ( value0.value != value1.value )
    elif op == '<=':
      resultValue = ( value0.value <= value1.value )
    elif op == '>=':
      resultValue = ( value0.value >= value1.value )
    elif op == '<':
      resultValue = ( value0.value < value1.value )
    elif op == '>':
      resultValue = ( value0.value > value1.value )
    else:
      raise Exception('Invalid comparison operand ({})'.format(op))
    return VariableRecord(TypeQuantifier.Const, DataType.Bool, resultValue)

  def visitBoolExp(self, ctx):
    value0 = self.visit(ctx.expression(0))
    value1 = self.visit(ctx.expression(1))
    assert(value0.dataType == value1.dataType and value0.dataType == DataType.Bool)
    op = ctx.binaryBoolOp().getText()
    resultValue = None
    if op == 'and':
      resultValue = ( value0.value and value1.value )
    elif op == 'or':
      resultValue = ( value0.value or value1.value )
    else:
      raise Exception('Invalid boolean operand ({})'.format(op))
    return VariableRecord(TypeQuantifier.Const, DataType.Bool, resultValue)

  def visitNegationExp(self, ctx):
    value = self.visit(ctx.expression())
    assert(value.dataType == DataType.Bool)
    value.value = (not value.value)
    return value

  def visitParenthesisExp(self, ctx):
    return self.visit(ctx.expression())

  def visitFuncCallExp(self, ctx):
    name = ctx.NamedValue().getText()
    record = self.getRecordFromName(name)
    if len(record.params) != len(ctx.args):
      raise Exception('Incorrect number of arguments for function {} (expected {} got {})'.format(name,len(record.params),len(ctx.args)))
    # create empty temporary environment to store arg values
    argsEnvironment = {}
    # evaluate arguments and store in temporary environment
    for param, arg in zip(record.params, ctx.args):
      argValue = self.visit(arg)
      argsEnvironment[param] = argValue
    # store current number of environments so that we can restore the same number on return
    currentNumOfEnv = len(self.environment)
    # push temporary environment to main environment
    self.environment.append(argsEnvironment)
    # run body and catch return value
    returnValue = None
    try:
      for statement in record.body:
        self.visit(statement)
    except FunctionReturnedException as returnException:
      returnValue = returnException.args[0]
    else:
      raise Exception('Function {} did not return a value'.format(name))
    if returnValue.dataType != record.dataType:
      raise Exception('Type mismatch in return value of function {} (expected {} got {})'.format(name,record.dataType.name,returnValue.dataType.name))
    # restore environment stack to correct state
    self.environment = self.environment[:currentNumOfEnv]
    return returnValue

  def visitSkipStmt(self, ctx):
    pass

  def visitValDeclStmt(self, ctx):
    name = ctx.NamedValue().getText()
    if name in self.environment[-1]:
      raise Exception('Name redefinition in same namespace ({})'.format(name))
    typeQuantifier = TypeQuantifier.parse(ctx.quantifiedType().typeQuantifier().getText())
    dataType = DataType.parse(ctx.quantifiedType().dataType().getText())
    value = self.visit(ctx.expression())
    if value.dataType != dataType:
      raise Exception('Type mismatch in assignment (assigning {} to {})'.format(value.dataType.name,dataType.name))
    self.environment[-1][name] = VariableRecord(typeQuantifier, dataType, value.value)

  def visitFuncDeclStmt(self, ctx):
    name = ctx.funcName.text
    if name in self.environment[-1]:
      raise Exception('Name redefinition in same namespace ({})'.format(name))
    body = ctx.statement()
    dataType = DataType.parse(ctx.funcRetType.getText())
    quantifiedTypes = ctx.funcArgTypes
    argNames = [name.text for name in ctx.funcArgNames]
    args = {}
    for argName, quantifiedType in zip(argNames, quantifiedTypes):
      if argName in args:
        raise Exception('Name redefinition among function arguments ({})'.format(argName))
      argTypeQuantifier = TypeQuantifier.parse(quantifiedType.typeQuantifier().getText())
      argDataType = DataType.parse(quantifiedType.dataType().getText())
      args[argName] = VariableRecord(argTypeQuantifier, argDataType, None)
    self.environment[-1][name] = FunctionRecord(dataType, args, body)

  def visitAssignStmt(self, ctx):
    name = ctx.NamedValue().getText()
    record = self.getRecordFromName(name)
    if TypeQuantifier.Var != record.typeQuantifier:
      raise Exception('Assignment to constant')
    value = self.visit(ctx.expression())
    if value.dataType != record.dataType:
      raise Exception('Type mismatch in assignment (assigning {} to {})'.format(value.dataType.name,dataType.name))
    record.value = value.value

  def visitPrintStmt(self, ctx):
    value = self.visit(ctx.expression())
    print(value.value)

  def visitIfElseStmt(self, ctx):
    condition = self.visit(ctx.expression())
    if condition.dataType != DataType.Bool:
      raise Exception('Condition is not a boolean')
    if condition.value == True:
      self.environment.append({})
      for statement in ctx.ifBlock:
        self.visit(statement)
      self.environment.pop()
    else:
      if len(ctx.elseBlock)>0:
        self.environment.append({})
        for statement in ctx.elseBlock:
          self.visit(statement)
        self.environment.pop()

  def visitWhileStmt(self, ctx):
    while True:
      condition = self.visit(ctx.expression())
      if condition.dataType != DataType.Bool:
        raise Exception('Condition is not a boolean')
      if condition.value == False:
        break
      self.environment.append({})
      for statement in ctx.statement():
        self.visit(statement)
      self.environment.pop()

  def visitReturnStmt(self, ctx):
    value = self.visit(ctx.expression())
    value.typeQuantifier = TypeQuantifier.Const
    # throw exception with return value, which will be caught by function call interpreter
    raise FunctionReturnedException(value)

  def interpret(self, ctx):
    self.environment = [{}]
    for statement in ctx.statement():
      self.visit(statement)

# I/O, lexing, parsing, then call interpreter
if __name__ == '__main__':
  # open and read file
  fileName = sys.argv[1]
  fileObj = open(fileName, 'r')
  programStr = fileObj.read()

  # lex and parse
  inputStream = InputStream(programStr)
  lexer = LangLexer(inputStream)
  tokenStream = CommonTokenStream(lexer)
  parser = LangParser(tokenStream)
  program = parser.program()

  # interpret
  interpreter = LangInterpreter()
  interpreter.interpret(program)

