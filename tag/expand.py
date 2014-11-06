import tag
import text
import lexer
import parser
import iteration

def token_class():
	return ExpandTagToken


class AbstractExpandToken(lexer.AbstractToken):

	def parse(self, context):
		try:
			start = context.defaultrange[0]
			end = context.defaultrange[1]
		except AttributeError:
			raise Exception("expansion directive requires a previously declared @defaultrange")

		counter = iteration.IterationCounter(start, end)

		inner_context = SimpleExpansionContext(self._rawcontent, context)
		inner_context.declare(counter.uniquename(), counter)
		inner_context.countername = counter.uniquename()

		content = inner_context.parse()

		return (counter, content)


'''
@expand is a simple repetition using the default range, substituting the innermost #
'''
class ExpandTagToken(tag.TagToken, AbstractExpandToken):

	def __init__(self, *args, **kwargs):
		tag.TagToken.__init__(self, *args, **kwargs)
	
	# Don't split args at commas
	@staticmethod
	def _lexer_split_args():
		return False

	def parse(self, context):

		if len(self.args) != 1:
			raise Exception("@expand expects exactly one argument")
		else:
			self._rawcontent = self.args[0]

		(counter, content) = AbstractExpandToken.parse(self, context)
		return iteration.IterationBlock(counter, content)


class SimpleExpansionContext(parser.ParsingContext):

	def parse_token(context, token):
		import text
		split_char = text.TextToken.split_char
		if isinstance(token, text.TextToken):
			# replace hash with an internal iteration variable name
			filtered_token = text.TextToken(token.line, token.char, token.text.replace('#', split_char + context.countername + split_char))
			return filtered_token.parse(context)
		else:
			return parser.ParsingContext.parse_token(context, token)
