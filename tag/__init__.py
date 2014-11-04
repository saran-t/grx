import lexer
import parser

tags = {}

def token_class(tagname):
	# Each tag type is defined as a python submodule with the same name
	try:
		return tags[tagname]

	except KeyError:
		try:
			return __import__('tag', globals(), locals(), [tagname], -1).__getattribute__(tagname).token_class()
		except Exception:
			return TagToken


def create_token(line, char, name, args = []):
	return token_class(name)(line, char, name, args)


class ExtendedTagContext(parser.ParsingContext):
	# subclass to enable @end tag
	def __init__(self, tokens, parent, tagtoken):
		parser.ParsingContext.__init__(self, tokens, parent)
		self.tagtoken = tagtoken


class TagToken(lexer.AbstractToken):
	def __init__(self, line, char, name, args = []):
		self.line = line
		self.char = char
		self.name = name
		self.args = args

	# The default behaviour is for the lexer to split argumentst list at commas
	# override this for special tags (e.g. @expand)
	@staticmethod
	def _lexer_split_args():
		return True

	def parse(self, context):
		raise Exception('unknown tag @' + self.name)

	def __repr__(self):
		return '<@' + self.name + '[' + repr(self.args) + ']>'


	def print_debug(self, prefix = ''):
		print repr(self.line) + ':' + repr(self.char) + ':\t' + prefix + '@' + self.name
		prefix = prefix.strip() + '>>>> '

		for (i, arg) in enumerate(self.args):
			print repr(arg[0].line) + ':' + repr(arg[0].char) + ':\t' + prefix + '[[ @' + self.name + '.args[' + str(i) + '] ]]'
			for token in arg:
				token.print_debug(prefix.strip() + '>>>> ')