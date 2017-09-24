import unittest
import copy

from spi import Token, BEGIN, END, VAR, ASSIGN, INTEGER, DOT, SEMI, ADD, DIV, MUL

class InterpreterTest(unittest.TestCase):
    def __init__(self, methodName):
        self.calc_cases = {
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
            '2*(-2)': -4,
            '4/-2': -2,
            '(5 + -1)/(2+ +2) + 2* -2 + 2+(-2)': -3,
            '(+1)+1': 2,
            '-(10*3)': -30,
            '+1+1': 2,
            '-1+1': 0,
            '5 - - - + - (3 + 4) - +2': 10
        }

        self.RPN_cases = {
            '1+1': '1 1 +',
            '(2+3)*2/5': '2 3 + 2 * 5 /',
            '+1': '1 +',
            '-1': '1 -'
        }

        self.list_expr_converter_caseses = {
            '1+1': '(+ 1 1)',
            '(2+3)*2/5': '(/ (* (+ 2 3) 2) 5)',
            '-1': '(- 1)',
            '+1': '(+ 1)'
        }

        self.spi_lexer_tests = {
            'BEGIN b := 10 * a + 10 * number / 4; END.' : [
                Token(BEGIN, 'BEGIN'),
                Token(VAR, 'b'),
                Token(ASSIGN, ':='),
                Token(INTEGER, 10),
                Token(MUL, '*'),
                Token(VAR, 'a'),
                Token(ADD, '+'),
                Token(INTEGER, 10),
                Token(MUL, '*'),
                Token(VAR, 'number'),
                Token(DIV, '/'),
                Token(INTEGER, 4),
                Token(SEMI, ';'),
                Token(END, 'END'),
                Token(DOT, '.'),
            ]
        }
        self.spi_cases = {
            'BEGIN BEGIN x := 2; END; number := x + 10; END.': {'x': 2, 'number': 12}
        }

        super(InterpreterTest, self).__init__(methodName)

    def calc_apply_test(self, text):
        from simple_calculator import Lexer, Parser, Interpreter
        lexer = Lexer(text)
        parser = Parser(lexer)
        ast = parser.parse()
        calc = Interpreter(ast)
        return calc.expr()

    def spi_apply_test(self, text):
        from spi import Lexer, Parser, Interpreter
        lexer = Lexer(text)
        parser = Parser(lexer)
        ast = parser.parse()
        spi = Interpreter(ast)
        spi.kickoff()
        return spi.getSymbols()

    def test_calc(self):
        print 'calculator test cases begin'
        for expr, result in self.calc_cases.iteritems():
            self.assertEqual(self.calc_apply_test(expr), result)
            print '{0} = {1}'.format(expr, result)
        print 'calculator test cases end\n'
    
    def test_rnpConverter(self):
        from simple_calculator import Lexer, Parser, RPNConverter
        print 'rpn test cases begin'
        for expr, result in self.RPN_cases.iteritems():
            lexer = Lexer(expr)
            parser = Parser(lexer)
            ast = parser.parse()
            rpn_converter = RPNConverter(ast)
            rpn = rpn_converter.get_rpn()
            self.assertEqual(result, rpn)
            print '{0} = {1}'.format(expr, result)
        print 'rpn test cases end\n'

    def test_listExprConverter(self):
        from simple_calculator import Lexer, Parser, ListExpressionConverter
        print 'list expr converter test cases begin'
        for expr, result in self.list_expr_converter_caseses.iteritems():
            lexer = Lexer(expr)
            parser = Parser(lexer)
            ast = parser.parse()
            list_expr_converter = ListExpressionConverter(ast)
            list_expr = list_expr_converter.get_list_expr()
            self.assertEqual(result, list_expr)
            print '{0} = {1}'.format(list_expr, result)
        print 'list expr converter test cases end\n'
    
    def test_spi_lexer(self):
        from spi import Lexer, Parser, ListExpressionConverter
        for line, values  in self.spi_lexer_tests.items():
            lexer = Lexer(line)
            for value in values:
                token = lexer.get_next_token()
                self.assertEqual(token.type, value.type)
                self.assertEqual(token.value, value.value)
                print '{0} = {1}'.format(token, value)

    def test_spi(self):
        import json
        print 'spi test cases begin'
        for expr, result in self.spi_cases.iteritems():
            spi_result = self.spi_apply_test(expr)
            spi_result = json.loads(spi_result)
            self.assertEqual(spi_result, result)
            print '{0} = {1}'.format(expr, result)
        print 'spi test cases end\n'


if __name__ == '__main__':
    unittest.main()
