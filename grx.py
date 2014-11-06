import sys
import lexer
import parser

'''
TODO: Change all exceptions raised by the lexer/parser to be of type GrxError
'''
class GrxError(Exception):
	pass


if len(sys.argv) == 1:
	print "Usage: python grx.py [input file] > [output file]"

else:
	try:
		tokens = lexer.lex(open(sys.argv[1]).read())
		blocks = parser.parse(tokens)
		print blocks.execute()

	except Exception, e:
		print(e.message)