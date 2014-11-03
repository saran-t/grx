import lexer
import parser
import text
import iteration

open_bracket_block = text.TextBlock('[')
close_bracket_block = text.TextBlock(']')


class ArrayExpandToken(lexer.AbstractToken):
	def __init__(self, line, char, content):
		self.line = line
		self.char = char
		self.content = content


	def __repr__(self):
		return '<[[' + repr(self.content) + ']]>'


	def print_debug(self, prefix = ''):
		print repr(self.line) + ':' + repr(self.char) + ':\t' + prefix + '[[ ArrayExpandToken ]]'
		for token in self.content:
			token.print_debug(prefix.strip() + '>>>> ')

	def parse(self, context):
		try:
			start = context.defaultrange[0]
			end = context.defaultrange[1]
		except AttributeError:
			raise Exception("array expansion directive requires a previously declared @defaultrange")

		counter = iteration.IterationCounter(start, end)

		inner_context = ArrayExpandContext(self.content, context)
		inner_context.declare(counter.uniquename(), counter)
		inner_context.countername = counter.uniquename()

		content = parser.BlockSequence([open_bracket_block, inner_context.parse(), close_bracket_block])

		context.append_block(iteration.IterationBlock(counter, content))


class ArrayExpandContext(parser.ParsingContext):

	def parse_token(context, token):
		import text
		if isinstance(token, text.TextToken):
			# replace hash with an internal iteration variable name
			filtered_token = text.TextToken(token.line, token.char, token.text.replace('#', '~' + context.countername + '~'))
			return text.parse_token(context, filtered_token)
		else:
			return parser.ParsingContext.parse_token(context, token)
