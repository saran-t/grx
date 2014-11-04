import tag.expand
import parser
import text
import iteration

open_bracket_block = text.TextBlock('[')
close_bracket_block = text.TextBlock(']')


class ArrayExpandToken(tag.expand.AbstractExpandToken):
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
		(counter, raw_content) = tag.expand.AbstractExpandToken.parse(self, context)

		# C array indexing goes backwards!
		(counter.start, counter.end, counter.stride) = (counter.end, counter.start, -1)

		content = parser.BlockSequence([open_bracket_block, raw_content, close_bracket_block])
		context.append_block(iteration.IterationBlock(counter, content))

