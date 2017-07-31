'''
A simple interpreter which can evaluate arithmetic expression containing +, -, *, /, (, ), and integers.
'''
INTEGER, PLUS, MINUS, MUL, DIV, EOF, L_PAR, R_PAR = 'INTEGER', 'PLUS', 'MINUS', 'MUL', 'DIV', 'EOF', 'L_PAR', 'R_PAR'

class Token(object):
    '''
    Token for arithmetic expression
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
        self.text = self.del_spaces(text)
        self.len = len(self.text)
        self.pos = 0
        self.current_char = self.text[0] if self.text else None

    @staticmethod
    def del_spaces(text):
        for char in ' \t\r\n':
            text = text.replace(char, '')
        return text

    #### scanner code
    def error(self, message):
        raise Exception(message)

    def advance(self):
        self.pos += 1
        if self.pos > self.len-1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def integer(self):
        start = self.pos
        while self.current_char and self.current_char.isdigit():
            self.advance()
        return int(self.text[start:self.pos])

    def get_next_token(self):
        if not self.current_char:
            return Token(EOF, None)
        elif self.current_char.isdigit():
            return Token(INTEGER, self.integer())
        elif self.current_char == '+':
            self.advance()
            return Token(PLUS, '+')
        elif self.current_char == '-':
            self.advance()
            return Token(MINUS, '-')
        elif self.current_char == '*':
            self.advance()
            return Token(MUL, '*')
        elif self.current_char == '/':
            self.advance()
            return Token(DIV, '/')
        elif self.current_char == '(':
            self.advance()
            return Token(L_PAR, '(')
        elif self.current_char == ')':
            self.advance()
            return Token(R_PAR, ')')
        else:
            self.error('Unrecognized char: {0}'.format(self.current_char))
            return Token(EOF, None)


class Interpreter(object):
    '''
    Parser for syntax analysis
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
            self.error('Unexpected token: {0}'.format(self.current_token))

    def term(self):
        result = self.factor()
        while True:
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
                result = result * self.factor()
            elif token.type == DIV:
                self.eat(DIV)
                result = result / self.factor()
            else:
                return result

    def factor(self):
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)
            return token.value
        elif token.type == L_PAR:
            self.eat(L_PAR)
            result = self.expr()
            self.eat(R_PAR)
            return result
        else:
            self.error('Unmatched parentheses')

    def expr(self):
        """Arithmetic expression parser / interpreter.
        expr   : term ((PLUS | MINUS) term)*
        term   : factor ((MUL | DIV) factor)*
        factor : INTEGER | (L_PAR expr R_PAR)
        """
        result = self.term()
        while self.current_token and self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            self.eat(token.type)
            if token.type == PLUS:
                result = result + self.term()
            elif token.type == MINUS:
                result = result - self.term()

        return result


def main():
    while True:
        text = raw_input("calc> ")
        if text == 'exit':
            return
        if not text:
            continue

        try:
            lexer = Lexer(text)
            calc = Interpreter(lexer)
            print calc.expr()
        except Exception, exp:
            print str(exp)


if __name__ == "__main__":
    main()