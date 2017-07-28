import unittest

class InterpreterTest(unittest.TestCase):
    def calc1_apply_test(self, text):
        from calc1 import Lexer, Interpreter
        lexer = Lexer(text)
        calc = Interpreter(lexer)
        return calc.expr()

    def spi_apply_test(self, text):
        from spi import Lexer, Parser, Interpreter
        lexer = Lexer(text)
        parser = Parser(lexer)
        ast = parser.parse()
        calc = Interpreter(ast)
        return calc.expr()

    cases = {
        '1+2': 3,
        '5-1': 4,
        '2*3': 6,
        '4/2': 2,
        '132-12': 120,
        '123+27': 150,
        '123*10': 1230,
        '147/3': 49,
        '(1+1)*2': 4,
        '(5-3)/2': 1,
        '3*(1-0)+ (2-1)/1 - 1* (12-11*(32-31*(32-20)/12))': 3,
        '(1+2)': 3,
        '(1+2)*(4+2)/2+1': 10
    }

    def test_calc1(self):
        for expr, result in self.cases.iteritems():
            self.assertEqual(self.calc1_apply_test(expr), result)

    def test_spi(self):
        for expr, result in self.cases.iteritems():
            print expr
            self.assertEqual(self.spi_apply_test(expr), result)


if __name__ == '__main__':
    unittest.main()
