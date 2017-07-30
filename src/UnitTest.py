import unittest
import copy

class InterpreterTest(unittest.TestCase):
    def __init__(self, methodName):
        self.common_cases = {
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
            '(((1+2)))': 3,
            '(1+2)*(4+2)/2+1': 10,
        }
        self.unary_cases = {
            '2*(-2)': -4,
            '4/-2': -2,
            '(5 + -1)/(2+ +2) + 2* -2 + 2+(-2)': -3,
            '(+1)+1': 2,
            '-(10*3)': -30,
            '+1+1': 2,
            '-1+1': 0
        }
        self.spi_cases = copy.copy(self.common_cases)
        self.spi_cases.update(self.unary_cases)
        super(InterpreterTest, self).__init__(methodName)

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


    def test_calc1(self):
        for expr, result in self.common_cases.iteritems():
            self.assertEqual(self.calc1_apply_test(expr), result)
            print '{0} = {1}'.format(expr, result)

    def test_spi(self):
        for expr, result in self.spi_cases.iteritems():
            self.assertEqual(self.spi_apply_test(expr), result)
            print '{0} = {1}'.format(expr, result)


if __name__ == '__main__':
    unittest.main()
