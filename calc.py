'''
Code which can only evaluate arithimetic expression containing +, - and integers.
'''
class Token(object):
    DIGITS = '0123456789'
    SPACES = ' \t\r\n'
    OPS = {
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
        '*': lambda x, y: x * y,
        '/': lambda x, y: x / y
    }

    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return "Token({0}, {1})".format(self.type, self.value)

    def __repr__(self):
        return self.__str__()


class Interpreter(object):
    def __init__(self, text):
        self.text = Interpreter.remove_spaces(text)
        self.pos = 0
        self.token = None
        self.value_stack = []
        self.op_stack = []

    @staticmethod
    def remove_spaces(text):
        for space in Token.SPACES:
            text = text.replace(space, '')
        return text

    @staticmethod
    def get_token_type(char):
        if char in Token.DIGITS:
            return 'int'
        elif char in Token.OPS:
            return 'op'
        else:
            return None

    def get_next_token(self):
        if self.pos >= len(self.text):
            return None

        text = self.text[self.pos:]
        token_type = Interpreter.get_token_type(text[0])
        token_end = len(text)
        for i, _ in enumerate(text):
            temp_token_type = Interpreter.get_token_type(text[i])
            if token_type != temp_token_type:
                token_end = i
                break
        self.pos += token_end
        value = text[:token_end]
        return Token(token_type, value)

    def token_generator(self):
        if not self.text:
            return
        text = self.text
        start = 0
        token_type = self.get_token_type(text[0])
        for i, char in enumerate(text):
            current_type = self.get_token_type(char)
            if current_type != token_type:
                value = text[start:i]
                yield Token(token_type, value)
                start = i
                token_type = current_type
        value = text[start:]
        yield Token(token_type, value)

    def error(self):
        raise Exception("Invalid token!")

    def eat(self, token):
        value = None
        if token.type == 'int':
            value = int(token.value)
            self.value_stack.append(value)
        elif token.type == 'op':
            value = Token.OPS[token.value]
            self.op_stack.append(value)

    def scan(self):
        while True:
            token = self.get_next_token()
            if not token:
                break
            self.eat(token)

    def scan1(self):
        for token in self.token_generator():
            self.eat(token)

    def eval_expr(self):
        while self.op_stack:
            operator = self.op_stack.pop()
            right = self.value_stack.pop()
            left = self.value_stack.pop()
            result = operator(left, right)
            self.value_stack.append(result)
        return self.value_stack.pop()

    def expr(self):
        self.scan1()
        return self.eval_expr()


PROMPT = 'calc> '


def main():
    while True:
        text = raw_input(PROMPT)
        if text == 'exit':
            return
        if text:
            calculator = Interpreter(text)
            try:
                result = calculator.expr()
            except Exception, exp:
                result = str(exp)
            finally:
                print result


if __name__ == '__main__':
    main()
