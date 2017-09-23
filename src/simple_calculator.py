'''
A simple interpreter which can evaluate integer arithmetic expression.
Code can be divided into Lexer, Parser and Interpreter.
It is the foundation of simple pacscal interpreter.
Grammars ->
    expr   : term ((ADD | SUB) term)*
    term   : factor ((MUL | DIV) factor)*
    factor : INTEGER | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
'''
import re


EOF = 'EOF'
INTEGER = 'INTEGER'
ADD, SUB, MUL, DIV = ('ADD', 'SUB', 'MUL', 'DIV')
L_PAR, R_PAR = ('L_PAR', 'R_PAR')
UNARY_ADD, UNARY_SUB = ('UNARY_ADD', 'UNARY_SUB')
UNARY_OP = (UNARY_ADD, UNARY_SUB)
BINARY_OP = (ADD, SUB, MUL, DIV)

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

    @staticmethod
    def del_spaces(text):
        text, _ = re.subn('\s', '', text)
        return text

    @property
    def current_char(self):
        return self.text[self.pos] if self.pos<self.len else None

    #### scanner code
    def error(self, message):
        raise Exception(message)

    def advance(self):
        self.pos += 1

    def integer(self):
        start = self.pos
        while self.current_char and self.current_char.isdigit():
            self.advance()
        return int(self.text[start:self.pos])

    def get_next_token(self):
        if not self.current_char:
            return Token(EOF, None)

        next_token = None
        if self.current_char.isdigit():
            next_token = Token(INTEGER, self.integer())
        else:
            if self.current_char == '+':
                if self.current_token and self.current_token.type in (R_PAR, INTEGER):
                    next_token = Token(ADD, '+')
                else:
                    next_token = Token(UNARY_ADD, '+')
            elif self.current_char == '-':
                if self.current_token and self.current_token.type in (R_PAR, INTEGER):
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
            self.advance()

        if next_token:
            self.current_token = next_token
            # print next_token
            return next_token

        self.error('Unrecognized char: {0}'.format(self.current_char))
        return Token(EOF, None)


class AST(object):
    '''
    Abstract Syntax Tree
    '''
    pass


class BinaryOp(AST):
    '''
    Binary operator node in abstract syntax tree
    '''
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = self.token = op


class Num(AST):
    '''
    Number node in abstract syntax tree
    '''
    def __init__(self, token):
        self.token = token


class UnaryOp(AST):
    '''
    Unary operator node in abstract syntax tree
    '''
    def __init__(self, token, operand):
        self.token = token
        self.operand = operand


class Parser(object):
    '''
    A integer arithmetic expression parser
    Grammars ->
    expr   : term ((ADD | SUB) term)*
    term   : factor ((MUL | DIV) factor)*
    factor : INTEGER | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
    '''
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = lexer.get_next_token()

    def error(self, message):
        raise Exception(message)

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error('Unexpected token: {0}. Expected: {1}'.format(self.current_token, token_type))

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
        factor: INTEGER | L_PAR expr R_PAR | (UNARY_ADD | UNARY_SUB) factor
        '''
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)
            return Num(token)
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

    def parse(self):
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
    Convert AST to List Expression
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
    
    def visit_BinaryOp(self, ast):
        op = ast.token.value
        left = self.visit(ast.left)
        right = self.visit(ast.right)
        return '({0} {1} {2})'.format(op, left, right)
    
    def visit_UnaryOp(self, ast):
        operand = self.visit(ast.operand)
        return '({0} {1})'.format(ast.token.value, operand)
    
    def visit_Num(self, ast):
        return '{0}'.format(ast.token.value)


class Interpreter(NodeVisitor):
    '''
    Interpreter for simple arithmetic expression
    '''
    def __init__(self, ast):
        self.ast = ast
    
    def visit_BinaryOp(self, ast):
        op = None
        if ast.token.type == ADD:
            op = lambda x,y: x+y
        elif ast.token.type == SUB:
            op = lambda x,y: x-y
        elif ast.token.type == MUL:
            op = lambda x,y: x*y
        elif ast.token.type == DIV:
            op = lambda x,y: x/y
        else:
            raise Exception("Unknown token: " + ast.token.type)
        
        left = self.visit(ast.left)
        right = self.visit(ast.right)
        return op(left, right)
    
    def visit_Num(self, ast):
        return ast.token.value

    def visit_UnaryOp(self, ast):
        op = None
        if ast.token.type == UNARY_SUB:
            op = lambda x: -x 
        elif ast.token.type == UNARY_ADD:
            op = lambda x: x
        else:
            raise Exception("Unknown token: " + ast.token.type)
        
        value = self.visit(ast.operand)
        return op(value)

    def expr(self):
        return self.visit(self.ast)

def evaluate(text):
    '''
    Shortcut to evaluate an integer arithmetic expression
    '''
    lexer = Lexer(text)
    parser = Parser(lexer)
    ast = parser.parse()
    calc = Interpreter(ast)
    return calc.expr()

def main():
    while True:
        text = raw_input("calc> ")
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
