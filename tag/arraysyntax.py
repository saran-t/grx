import tag
import text

def token_class():
	return ArraySyntaxTagToken


class ArraySyntaxTagToken(tag.TagToken):

	def parse(self, context):
		if len(self.args) != 1:
			raise ValueError("@arraysyntax takes exactly one argument")

		syntax = text.PlainStringContext(self.args[0], context).parse().strip().upper()
		
		if syntax == 'C':
			context.arraysyntax = 'C'
		elif syntax == 'F' or syntax == 'F90' or syntax == 'FORTRAN':
			context.arraysyntax = 'F'
		else:
			raise Exception("unknown array syntax " + syntax)