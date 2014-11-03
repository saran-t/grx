import re
from lexer import AbstractToken
from parser import ParsingContext, AbstractBlock, BlockSequence

tilde = re.compile(r"~")


def blockify(content):
	if isinstance(content, AbstractBlock):
		return content
	else:
		return TextBlock(content)


class PlainStringContext(ParsingContext):

	def parse_all(self):
		text = ''

		for token in self.tokens_iterator:
			if not isinstance(token, TextToken):
				raise Exception('not a plain string')
			else:
				text = text + token.text

		return text


class TextToken(AbstractToken):
	def __init__(self, line, char, text):
		self.line = line
		self.char = char
		self.text = text

	def parse(self, context):
		blocks = []

		pieces = tilde.split(self.text)
		for piece in pieces:

			var = context.getvar(piece)
			if var is None:
				if len(blocks) > 0 and isinstance(blocks[-1], TextBlock):
					blocks[-1].append('~').append(piece)
				else:
					blocks.append(TextBlock(piece))
			else:
				blocks.append(var)

		context.append_block(BlockSequence(blocks))

	def __repr__(self):
		return '<TextToken>'

	def print_debug(self, prefix = ''):
		print repr(self.line) + ':' + repr(self.char) + ':\t' + prefix + self.text


class TextBlock(AbstractBlock):
	content = ''

	def __init__(self, content):
		self.content = str(content)

	def append(self, content):
		self.content = self.content + str(content)
		return self

	def execute(self):
		return self.content

