INTEGER, PLUS, MINUS, EOF = 'INTEGER', 'PLUS', 'MINUS', 'EOF'

class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return 'Token({0}, {1})'.format(self.type, self.value)

    def __str__(self):
        return self.__repr__()

class Interpreter(object):
    def __init__(self, text):
        self.text = self.del_spaces(text)
        self.len = len(self.text)
        self.pos = 0
        self.current_token = None
        self.current_char = self.text[0] if self.text else None
    
    @staticmethod
    def del_spaces(text):
        for char in ' \t\r\n':
            text = text.replace(char, '')
        return text

    #### scanner code
    def error(self):
        raise Exception("Invalid Syntax!")
    
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
        else:
            self.error()
            return Token(EOF, None)

    #### parser code
    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error()

    def term(self):
        token = self.current_token
        self.eat(INTEGER)
        return token.value

    def expr(self):
        self.current_token = self.get_next_token()
        result = self.term()

        while self.current_token and self.current_token.type in (PLUS, MINUS):
            if self.current_token.type == PLUS:
                self.eat(PLUS)
                result = result + self.term()
            elif self.current_token.type == MINUS:
                self.eat(MINUS)
                result = result - self.term()
            else:
                self.error()
        
        return result


def main():
    while True:
        text = raw_input("calc> ")
        if text == 'exit':
            return
        if not text:
            continue

        try:
            calc = Interpreter(text)
            print calc.expr()
        except Exception, exp:
            print str(exp)


if __name__ == "__main__":
    main()
