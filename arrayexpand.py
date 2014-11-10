import tag.expand
import parser
import text
import iteration

class ArrayExpandToken(tag.expand.AbstractExpandToken):
	def __init__(self, line, char, content):
		self.line = line
		self.char = char
		self._rawcontent = content

	def __repr__(self):
		return '<[[' + repr(self._rawcontent) + ']]>'

	def print_debug(self, prefix = ''):
		print repr(self.line) + ':' + repr(self.char) + ':\t' + prefix + '[[ ArrayExpandToken ]]'
		for token in self.content:
			token.print_debug(prefix.strip() + '>>>> ')

	def parse(self, context):
		(counter, content) = tag.expand.AbstractExpandToken.parse(self, context)

		if not hasattr(context, 'arraysyntax'):
			raise Exception("[[...]] array expansion used without a previously defined @arraysyntax")
		elif context.arraysyntax == 'C':
			# C array indexing goes backwards!
			(counter.start, counter.end, counter.stride) = (counter.end, counter.start, -1)
			return iteration.IterationBlock(counter, content, formatstring = '[%s]')

		elif context.arraysyntax == 'F':
			return iteration.IterationBlock(counter, content, before = '(', between = ',', after = ')')
			
		
