'''
A simple interpreter which can evaluate integer arithmetic expression.
Code is refactored into Lexer, Parser and Interpreter.

Code sample:
PROGRAM main;
VAR
   number     : INTEGER;
   a, b, c, x : INTEGER;
   y          : REAL;

BEGIN {Part10}
   BEGIN
      number := 2;
      a := number;
      b := 10 * a + 10 * number div 4;
      c := a - - b
   END;
   x := 11;
   y := 20 / 7 + 3.14;
   { writeln('a = ', a); }
   { writeln('b = ', b); }
   { writeln('c = ', c); }
   { writeln('number = ', number); }
   { writeln('x = ', x); }
   { writeln('y = ', y); }
END.  {main}

Grammars ->
    program             : PROGRAM name SEMI block DOT
    block               : declarations compound_statement
    declarations        : DECLARE_START (var_declarations SEMI)+ | EMPTY
    var_declarations    : VAR (COMMA VAR)* COLON type_name
    type_name           : INTEGER | REAL
    compound_statement  : BEGIN statement_list END
    statement_list      : statement | statement SEMI statement_list
    statement           : compound_statement | assignment | empty
    assignment          : VAR ASSIGN expr
    expr                : term ((ADD | SUB) term)*
    term                : factor ((MUL | INT_DIV | FLOAT_DIV) factor)*
    factor              : INTEGER_CONST | REAL_CONST | VAR | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
'''
import re
import sys
import logging

logging.getLogger().setLevel(logging.NOTSET)


EOF = 'EOF'
SEMI = 'SEMI'
EMPTY = 'EMPTY'
DOT = 'DOT'
COMMENT = 'COMMENT' # string starting with '{' and ending with '}'

# Names of keywors are set as the same value as the literals in the program
KEY_WORDS = (PROGRAM_START, BEGIN, END, DECLARE_START, INT_DIV, INT_TYPE, REAL_TYPE) = ('program', 'begin', 'end', 'var', 'div', 'integer', 'real')

INTEGER_CONST = 'INTEGER_CONST'
REAL_CONST = 'REAL_CONST'
VAR = 'VAR'

# + - * div := : ,
BINARY_OP = (ADD, SUB, MUL, INT_DIV, FLOAT_DIV, ASSIGN, COLON, COMMA) = ('ADD', 'SUB', 'MUL', 'div', 'FLOAT_DIV', 'ASSIGN', 'COLON', 'COMMA')
UNARY_OP = (UNARY_ADD, UNARY_SUB) = ('UNARY_ADD', 'UNARY_SUB')
NARY_OP = (COMPOUND, ) = ('COMPOUND', )

L_PAR, R_PAR = ('L_PAR', 'R_PAR')

class Token(object):
    '''
    Token for integer arithmetic expressions
    '''
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return 'Token({0}, {1})'.format(self.type, self.value)

    def __str__(self):
        return self.__repr__()


class Lexer(object):
    '''
    Scanner: get tokens from the code
    '''
    blank_pattern = re.compile(r'^\s+')
    def __init__(self, text):
        # in case text is not a string, such as None or a integer
        self.text = text.strip().lower() if isinstance(text, str) else ''
        self.len = len(self.text)
        self.pos = 0
        self.current_token = None
        self.peeked = None
    
    @property
    def non_scanned(self):
        '''
        The part of the input code that has not been tokenized
        '''
        # it is safe even if self.text is ''
        return self.text[self.pos:]

    @property
    def scanned(self):
        '''
        The part of the input code that has been tokenized
        '''
        # it is safe even if self.text is ''
        return self.text[0:self.pos]

    @property
    def current_char(self):
        return self.text[self.pos] if self.pos<self.len else None

    #### scanner code
    def error(self, message):
        raise Exception(message)

    def advance(self, steps=1):
        self.pos += steps
        if self.pos > self.len:
            self.pos = self.len-1

    def _try_get(self, pattern):
        match = pattern.match(self.non_scanned)
        if match:
            identifier = match.group()
            return identifier
        else:
            return None

    def try_get_identifier(self):
        pattern = re.compile(r'^[_a-z]\w*')
        return self._try_get(pattern)
    
    def try_get_float(self):
        pattern = re.compile(r'\d+\.\d+')
        return self._try_get(pattern)

    def try_get_int(self):
        pattern = re.compile(r'\d+')
        return self._try_get(pattern)

    def peek(self):
        '''
        Methods in peek call stack must not alter self.pos
        '''
        if self.non_scanned.startswith(':='):
            self.peeked = Token(ASSIGN, ':=')
            return True

        if self.current_char.isdigit():
            real = self.try_get_float()
            if real:
                self.peeked = Token(REAL_CONST, real)
            else:
                integer = self.try_get_int()
                self.peeked = Token(INTEGER_CONST, integer)
            return True

        idf = self.try_get_identifier()
        if idf:
            if idf in KEY_WORDS:
                if idf == 'div':
                    self.peeked = Token(INT_DIV, idf)
                else:
                    # type and value of  keywords token are the same
                    self.peeked = Token(idf, idf)
            else:
                self.peeked = Token(VAR, idf)
            return True
        return False
    
    def comment(self):
        '''
        currently only single layer comments '{comments}' are handled, 
        not work with comments like "{{comments}}"
        '''
        start = self.pos
        while self.current_char and self.current_char != '}':
            self.advance()
        if self.current_char:
            self.advance()
            return self.text[start: self.pos+1]
        else:
            self.error('Invalid comment: {}'.format(self.text[start:]))

    def get_next_token(self):
        if not self.current_char:
            return Token(EOF, None)

        while self.blank_pattern.match(self.current_char):
            # print 'blank'
            self.advance()

        next_token = None
        if self.current_char == '{':
            comm = self.comment()
            next_token = Token(COMMENT, comm)
        elif self.peek():
            next_token = self.peeked
            value = next_token.value
            self.advance(steps=len(value))
        else:
            if self.current_char == '+':
                if self.current_token and self.current_token.type in (R_PAR, INTEGER_CONST, VAR):
                    next_token = Token(ADD, '+')
                else:
                    next_token = Token(UNARY_ADD, '+')
            elif self.current_char == '-':
                if self.current_token and self.current_token.type in (R_PAR, INTEGER_CONST, VAR):
                    next_token = Token(SUB, '-')
                else:
                    next_token = Token(UNARY_SUB, '-')
            elif self.current_char == '*':
                next_token = Token(MUL, '*')
            elif self.current_char == '/':
                next_token = Token(FLOAT_DIV, '/')
            elif self.current_char == '(':
                next_token = Token(L_PAR, '(')
            elif self.current_char == ')':
                next_token = Token(R_PAR, ')')
            elif self.current_char == '.':
                next_token = Token(DOT, '.')
            elif self.current_char == ';':
                next_token = Token(SEMI, ';')
            elif self.current_char == ',':
                next_token = Token(COMMA, ',')
            # ASSIGN ':=' tested in peek(), so if ':' here is COLON
            elif self.current_char == ':':
                next_token = Token(COLON, ':')
            self.advance()

        if next_token:
            self.current_token = next_token
            return next_token

        self.error('Unrecognized char: {0}.'.format(self.current_char))
        return Token(EOF, None)


# AST base class and derived classes begin here
class AST(object):
    '''
    Abstract Syntax Tree
    '''
    pass


class Empty(AST):
    def __init__(self, token):
        self.token = token


class Num(AST):
    '''
    Number node in abstract syntax tree
    '''
    def __init__(self, token):
        if token.type not in (INTEGER_CONST, REAL_CONST):
            raise Exception("Token mismatch: expected {0}, got {1}".format(INTEGER_CONST, token))
        self.token = token


class Variable(AST):
    '''
    Variable node in AST
    '''
    def __init__(self, token):
        if token.type != VAR:
            raise Exception("Token mismatch: expected {0}, got {1}".format(VAR, str(token)))
        self.token = token

class Type(AST):
    '''
    Type node in AST
    '''
    def __init__(self, token):
        if token.type not in (INT_TYPE, REAL_TYPE):
            raise Exception("Token mismatch: expected type token, got {1}".format(token))
        self.token = token

class UnaryOp(AST):
    '''
    Unary operator node in AST
    '''
    def __init__(self, token, operand):
        if token.type not in UNARY_OP:
            raise Exception("Token mismatch: expected unary, got {}".format(token))
        self.token = token
        self.operand = operand


class BinaryOp(AST):
    '''
    Binary operator node in AST
    '''
    def __init__(self, left, right, token):
        if token.type not in BINARY_OP:
            raise Exception("Token mismatch: expected binary, got {}".format(token))
        self.left = left
        self.right = right
        self.op = self.token = token


class CompoundOp(AST):
    '''
    Operator with more than 2 operands in AST
    '''
    def __init__(self, operands, token):
        '''
        operands: a list containing the operands by the order left to right
        '''
        if token.type not in NARY_OP:
            raise Exception("Token mismatch: expected nary, got {}".format(token))
        self.operands = operands
        self.op = self.token = token

# AST base class and derived classes end here


class SymbolTable(object):
    def __init__(self):
        self.table = {}

    def assign(self, var_name, value):
        self.table.setdefault(var_name, [None, None])[1] = value
        return value

    def declare(self, var_name, type_name):
        self.table.setdefault(var_name, [None, None])[0] = type_name
    
    def lookup(self, var_name):
        if var_name not in self.table:
            raise Exception("Name {} is not defined".format(var_name))
        return self.table.get(var_name)

    def getSymbols(self):
        import json
        return json.dumps(self.table)


class Parser(object):
    '''
    A simple pascal parser
    Grammars ->
    program             : compound_statement DOT
    compound_statement  : BEGIN statement_list END
    statement_list      : statement | statement SEMI statement_list
    statement           : compound_statement | assignment | empty
    assignment          : VAR ASSIGN expr
    expr                : term ((ADD | SUB) term)*
    term                : factor ((MUL | INT_DIV) factor)*
    factor              : INTEGER_CONST | VAR | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
    '''
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = lexer.get_next_token()
        self.peeked_tokens = []
    
    def error(self, message):
        '''
        Report an error
        '''
        raise Exception(message)
    
    def get_next_token(self):
        token = self.lexer.get_next_token()
        while token.type == COMMENT:
            token = self.lexer.get_next_token()
        return token

    def eat(self, token_type):
        '''
        Try to get the next token with type token_type
        '''
        saved_token = self.current_token
        if self.current_token.type == token_type:
            if self.peeked_tokens:
                self.current_token = self.peeked_tokens[0]
                self.peeked_tokens.remove(self.current_token)
            else:
                self.current_token = self.get_next_token()
            logging.info("Eat token %s", self.current_token)
        else:
            self.error('Unexpected token: {0}. Expected: {1}'.format(self.current_token, token_type))
        return saved_token
        
    
    def peek(self):
        token = self.get_next_token()
        self.peeked_tokens.append(token)
        return token

    def parse(self):
        return self.program()

    def program(self):
        '''
        program: PROGRAM name SEMI block DOT
        '''
        if self.current_token.type != PROGRAM_START:
            self.error("Program not defined")
        self.eat(PROGRAM_START)
        self.eat(VAR)
        self.eat(SEMI)
        root = self.block()
        self.eat(DOT)
        return root

    def block(self):
        '''   
        block: declarations compound_statement
        '''
        dec = self.declarations()
        comp = self.compound_statement()
        return CompoundOp([dec, comp], Token(COMPOUND, 'program'))

    def declarations(self):
        '''
        declarations: DECLARE_START (var_declarations SEMI)+ | EMPTY
        '''
        self.eat(DECLARE_START)
        operands = []
        element = self.var_declarations()
        self.eat(SEMI)
        operands.append(element)
        while self.current_token.type == VAR:
            element = self.var_declarations()
            self.eat(SEMI)
            operands.append(element)
        return CompoundOp(operands, Token(COMPOUND, 'VAR'))

    def var_declarations(self):
        '''
        var_declarations: VAR (COMMA VAR)* COLON type_name
        '''
        left = self.variable()
        while self.current_token.type == COMMA:
            op = self.eat(COMMA)
            right = self.variable()
            left = BinaryOp(left, right, op)
        op = self.eat(COLON)
        typename = self.type_name()
        return BinaryOp(left, typename, op)

    def type_name(self):
        '''
        type_name: INT_TYPE | REAL_TYPE
        '''
        if self.current_token.type in (INT_TYPE, REAL_TYPE):
            type_token =  self.eat(self.current_token.type)
            return Type(type_token)
        else:
            self.error("Unknown type: {}".format(self.current_token.value))
    
    def compound_statement(self):
        '''
        compound_statement: BEGIN statement_list END
        '''
        self.eat(BEGIN)
        st_list = []
        self.statement_list(st_list)
        self.eat(END)
        token = Token(COMPOUND, 'COMPOUND')
        return CompoundOp(st_list, token)
    
    def statement_list(self, st_list):
        '''
        statement_list: statement | statement SEMI statement_list
        '''
        st = self.statement()
        st_list.append(st)
        if self.current_token.type != SEMI:
            return st_list

        self.eat(SEMI)
        self.statement_list(st_list)
    
    def statement(self):
        '''
        statement: compound_statement | assignment | empty
        '''
        # compound_satement next
        if self.current_token.type == BEGIN:
            return self.compound_statement()
        # assignment next
        elif self.current_token.type == VAR:
            return self.assignment()
        else:
            return self.empty()

    def empty(self):
        return Empty(Token(EMPTY, 'EMPTY'))
    
    def assignment(self):
        """
        assignment : VAR ASSIGN expr
        """
        var = self.variable()
        assign_token = self.eat(ASSIGN)
        right_operand = self.expr()
        assign = BinaryOp(var, right_operand, assign_token)
        return assign

    def variable(self):
        token = self.eat(VAR)
        return Variable(token)

    def expr(self):
        """
        expr: term ((ADD | SUB) term)*
        """
        left = self.term()
        while self.current_token and self.current_token.type in (ADD, SUB):
            token = self.current_token
            self.eat(token.type)
            right = self.term()
            left = BinaryOp(left, right, token)
        return left

    def term(self):
        '''
        term: factor ((MUL | INT_DIV | FLOAT_DIV) factor)*
        '''
        left = self.factor()
        while self.current_token.type in (MUL, INT_DIV, FLOAT_DIV):
            token = self.current_token
            self.eat(token.type)
            right = self.factor()
            left = BinaryOp(left, right, token)
        return left

    def factor(self):
        '''
        factor: INTEGER_CONST | REAL_CONST | VAR | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
        '''
        token = self.current_token
        if token.type in (INTEGER_CONST, REAL_CONST):
            self.eat(token.type)
            return Num(token)
        elif token.type == VAR:
            self.eat(VAR)
            return Variable(token)
        elif token.type == L_PAR:
            self.eat(L_PAR)
            node = self.parse()
            self.eat(R_PAR)
            return node
        elif token.type in (UNARY_ADD, UNARY_SUB):
            self.eat(token.type)
            operand = self.factor()
            return UnaryOp(token, operand)
        else:
            self.error('Unmatched parentheses')


class NodeVisitor(object):
    '''
    Dispatch a visit to a specific AST node to a specialized method
    '''
    def __init__(self):
        pass

    def visit(self, ast):
        '''
        Call visit methods per type of token stored in the node
        '''
        func_name = 'visit_' + type(ast).__name__
        func = getattr(self, func_name)
        return func(ast)

class RPNConverter(NodeVisitor):
    '''
    Convert AST to Reverse Polish Notation
    '''
    def __init__(self, ast):
        '''
        set abstract syntax tree
        '''
        self.ast = ast
    
    def get_rpn(self):
        '''
        get reverse polish notation
        '''
        return self.visit(self.ast)
    
    def visit_BinaryOp(self, ast):
        left = self.visit(ast.left)
        right = self.visit(ast.right)
        return '{0} {1} {2}'.format(left, right, ast.token.value)
    
    def visit_UnaryOp(self, ast):
        operand = self.visit(ast.operand)
        return '{0} {1}'.format(operand, ast.token.value)
    
    def visit_Num(self, ast):
        return '{0}'.format(ast.token.value)


class ListExpressionConverter(NodeVisitor):
    '''
    Convert AST to List Expression, such as:
    1 + 2 => (+ 1 2)
    '''
    def __init__(self, ast):
        '''
        set abstract syntax tree
        '''
        self.ast = ast
    
    def get_list_expr(self):
        '''
        get list expression
        '''
        return self.visit(self.ast)
    
    def visit_Num(self, ast):
        return '{0}'.format(ast.token.value)

    def visit_UnaryOp(self, ast):
        operand = self.visit(ast.operand)
        return '({0} {1})'.format(ast.token.value, operand)
    
    def visit_BinaryOp(self, ast):
        op = ast.token.value
        left = self.visit(ast.left)
        right = self.visit(ast.right)
        return '({0} {1} {2})'.format(op, left, right)


class Interpreter(NodeVisitor):
    '''
    Interpreter for simple pascal program
    '''
    def __init__(self, ast):
        self.ast = ast
        self.table = SymbolTable()
    
    def save(self, var_name, value):
        return self.table.assign(var_name, value)
    def lookup(self, var_name):
        return self.table.lookup(var_name)[1]
    def declare(self, var_name, type_name):
        return self.table.declare(var_name, type_name)
    def getSymbols(self):
        return self.table.getSymbols()

    def visit_Empty(self, ast):
        return ast.token.value

    def visit_Type(self, ast):
        return ast.token.value

    def visit_Num(self, ast):
        if ast.token.type == INTEGER_CONST:
            return int(ast.token.value)
        elif ast.token.type == REAL_CONST:
            return float(ast.token.value)
        self.error("Error in visit_Num: get token: {}.".format(ast.token))

    def visit_Variable(self, ast):
        token = ast.token
        return token.value

    def visit_UnaryOp(self, ast):
        op = None
        token = ast.token
        if token.type == UNARY_SUB:
            op = lambda x: -x 
        elif token.type == UNARY_ADD:
            op = lambda x: x
        else:
            raise Exception("Unknown token: ".format(token))
        
        operand = ast.operand
        value = self.visit(operand)
        if isinstance(operand, Variable):
            value = self.lookup(value)
        
        return op(value)
    
    def visit_BinaryOp(self, ast):
        op = None
        token = ast.token

        if token.type == ASSIGN:
            left = self.visit(ast.left)
            right = self.visit(ast.right)
            if isinstance(ast.right, Variable):
                right = self.lookup(right)
            return self.save(left, right)
        elif token.type == COMMA:
            def comma(x, y):
                if isinstance(x, list) and isinstance(y, list):
                    return x + y
                elif isinstance(x, list):
                    x.append(y)
                    return x
                elif isinstance(y, list):
                    y.append(x)
                    return y
                return [x, y]
            left = self.visit(ast.left)
            right = self.visit(ast.right)
            return comma(left, right)
        elif token.type == COLON:
            def colon(x, y):
                if isinstance(x, list):
                    for i in x:
                        self.declare(i, y)
                else:
                    self.declare(x, y)
            left = self.visit(ast.left)
            right = self.visit(ast.right)
            return colon(left, right)

        if token.type == ADD:
            op = lambda x,y: x+y
        elif token.type == SUB:
            op = lambda x,y: x-y
        elif token.type == MUL:
            op = lambda x,y: x*y
        elif token.type == INT_DIV:
            op = lambda x,y: x/y
        elif token.type == FLOAT_DIV:
            op = lambda x,y: (x*1.0)/y
        else:
            raise Exception("Unknown token: {}".format(token))
        
        left = self.visit(ast.left)
        if isinstance(ast.left, Variable):
            left = self.lookup(left)
        right = self.visit(ast.right)
        if isinstance(ast.right, Variable):
            right = self.lookup(right)
        return op(left, right)

    def visit_CompoundOp(self, ast):
        op = None
        token = ast.token
        if token.type == COMPOUND:
            for ast_node in ast.operands:
                value = self.visit(ast_node)
            return value
        else:
            raise Exception("Unknown token: {}".format(token))

    def kickoff(self):
        return self.visit(self.ast)

def test_lexer(file=None):
    if not file:
        file = 'code.pas'
    with open(file) as fd:
        text = fd.read()
    lexer = Lexer(text)

    while True:
        token = lexer.get_next_token()
        print token
        if token.type == EOF:
            break

def evaluate(file=None):
    '''
    Shortcut to evaluate a simple pascal program
    '''
    if not file:
        file = 'code.pas'
    with open(file) as fd:
        text = fd.read()

    lexer = Lexer(text)
    parser = Parser(lexer)
    ast = parser.parse()
    interpreter = Interpreter(ast)
    interpreter.kickoff()
    return interpreter.getSymbols()

def main():
    # if len(sys.argv)!=2:
    #     print 'Usage: python spi.py <pascal source file>'
    #     return 
    try:
        # symbol_table = evaluate(sys.argv[1])
        symbol_table = evaluate()
        print symbol_table
    except Exception, exp:
        print str(exp)


if __name__ == "__main__":
    main()
