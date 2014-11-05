import lexer
import parser

tokens = lexer.lex(open('sample/test2.c.grx').read())
blocks = parser.parse(tokens)
print blocks.execute()
