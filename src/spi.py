'''
A simple interpreter which can evaluate integer arithmetic expression.
Code is refactored into Lexer, Parser and Interpreter.

Code sample:
BEGIN
    BEGIN
        number := 2;
        a := number;
        b := 10 * a + 10 * number / 4;
        c := a - - b
    END;
    x := 11;
END.

Grammars ->
    program             : compound_statement DOT
    compound_statement  : BEGIN statement_list END
    statement_list      : statement | statement SEMI statement_list
    statement           : compound_statement | assignment | empty
    assignment          : VAR ASSIGN expr
    expr                : term ((ADD | SUB) term)*
    term                : factor ((MUL | DIV) factor)*
    factor              : INTEGER | VAR | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
'''
import re
import logging

logging.getLogger().setLevel(logging.NOTSET)


EOF = 'EOF'
SEMI = 'SEMI'
EMPTY = 'EMPTY'
DOT = 'DOT'
KEY_WORDS = (BEGIN, END) = ('BEGIN', 'END')

INTEGER = 'INTEGER'
VAR = 'VAR'

BINARY_OP = (ADD, SUB, MUL, DIV, ASSIGN) = ('ADD', 'SUB', 'MUL', 'DIV', 'ASSIGN')
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
    def __init__(self, text):
        # in case text is not a string, such as None or a integer
        self.text = self.del_spaces(text) if isinstance(text, str) else ''
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

    @staticmethod
    def del_spaces(text):
        text, _ = re.subn('\s', '', text)
        return text

    #### scanner code
    def error(self, message):
        raise Exception(message)

    def advance(self, steps=1):
        self.pos += steps

    def integer(self):
        start = self.pos
        while self.current_char and self.current_char.isdigit():
            self.advance()
        return int(self.text[start:self.pos])

    def keyword(self):
        for word in KEY_WORDS:
            if self.non_scanned.startswith(word):
                self.peeked = Token(word, word)
                return True
        return False

    def variable(self):
        pattern = re.compile(r'^\w+')
        match = pattern.match(self.non_scanned)
        if match:
            var = match.group()
            self.peeked = Token(VAR, var)
            return True
        else:
            return False

    def peek(self):
        if self.non_scanned.startswith(':='):
            self.peeked = Token(ASSIGN, ':=')
            return True
        else:
            return self.keyword() or self.variable()

    def get_next_token(self):
        if not self.current_char:
            return Token(EOF, None)

        next_token = None
        if self.current_char.isdigit():
            next_token = Token(INTEGER, self.integer())
        elif self.peek():
            next_token = self.peeked
            value = next_token.value
            self.advance(steps=len(value))
        else:
            if self.current_char == '+':
                if self.current_token and self.current_token.type in (R_PAR, INTEGER, VAR):
                    next_token = Token(ADD, '+')
                else:
                    next_token = Token(UNARY_ADD, '+')
            elif self.current_char == '-':
                if self.current_token and self.current_token.type in (R_PAR, INTEGER, VAR):
                    next_token = Token(SUB, '-')
                else:
                    next_token = Token(UNARY_SUB, '-')
            elif self.current_char == '*':
                next_token = Token(MUL, '*')
            elif self.current_char == '/':
                next_token = Token(DIV, '/')
            elif self.current_char == '(':
                next_token = Token(L_PAR, '(')
            elif self.current_char == ')':
                next_token = Token(R_PAR, ')')
            elif self.current_char == '.':
                next_token = Token(DOT, '.')
            elif self.current_char == ';':
                next_token = Token(SEMI, ';')
            self.advance()

        if next_token:
            self.current_token = next_token
            return next_token

        self.error('Unrecognized char: {0}'.format(self.current_char))
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
        if token.type != INTEGER:
            raise Exception("Token mismatch: expected {0}, got {1}".format(INTEGER, token))
        self.token = token


class Variable(AST):
    '''
    Variable node in AST
    '''
    def __init__(self, token):
        if token.type != VAR:
            raise Exception("Token mismatch: expected {0}, got {1}".format(VAR, str(token)))
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

    def save(self, var_name, value):
        self.table[var_name] = value
        return value
    
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
    term                : factor ((MUL | DIV) factor)*
    factor              : INTEGER | VAR | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
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
                self.current_token = self.lexer.get_next_token()
            logging.info("Eat token %s", self.current_token)
        else:
            self.error('Unexpected token: {0}. Expected: {1}'.format(self.current_token, token_type))
        return saved_token
        
    
    def peek(self):
        token = self.lexer.get_next_token()
        self.peeked_tokens.append(token)
        return token

    def parse(self):
        return self.program()

    def program(self):
        root = self.compound_statement()
        self.eat(DOT)
        return root
    
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
        term: factor ((MUL | DIV) factor)*
        '''
        left = self.factor()
        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            self.eat(token.type)
            right = self.factor()
            left = BinaryOp(left, right, token)
        return left

    def factor(self):
        '''
        factor: INTEGER | VAR | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
        '''
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)
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
        return self.table.save(var_name, value)
    def lookup(self, var_name):
        return self.table.lookup(var_name)
    def getSymbols(self):
        return self.table.getSymbols()

    def visit_Empty(self, ast):
        return ast.token.value

    def visit_Num(self, ast):
        return ast.token.value

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
        if token.type == ADD:
            op = lambda x,y: x+y
        elif token.type == SUB:
            op = lambda x,y: x-y
        elif token.type == MUL:
            op = lambda x,y: x*y
        elif token.type == DIV:
            op = lambda x,y: x/y
        elif token.type == ASSIGN:
            op = lambda x,y: self.save(x, y)
            left = self.visit(ast.left)
            right = self.visit(ast.right)
            return op(left, right)
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

def evaluate(text=None):
    '''
    Shortcut to evaluate a simple pascal program
    '''
    text = open('pascal.txt').read()
    lexer = Lexer(text)
    parser = Parser(lexer)
    ast = parser.parse()
    interpreter = Interpreter(ast)
    interpreter.kickoff()
    return interpreter

def main():
    while True:
        text = raw_input("pascal> ")
        if text == 'exit':
            return
        if not text:
            continue
        try:
            print evaluate(text)
        except Exception, exp:
            print str(exp)


if __name__ == "__main__":
    main()
