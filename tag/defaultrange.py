import tag
import text

def token_class():
	return DefaultRangeTagToken

class DefaultRangeTagToken(tag.TagToken):
	def parse(self, context):
		if len(self.args) != 2:
			raise ValueError("@defaultrange takes exactly two arguments")

		start = NonNegativeIntegerContext(self.args[0], context).parse()
		end = NonNegativeIntegerContext(self.args[1], context).parse()

		context.defaultrange = [start, end]

class NonNegativeIntegerContext(text.PlainStringContext):
	def parse_all(self):
		numstring = text.PlainStringContext.parse_all(self)

		try:
			num = int(numstring)
			if num < 0:
				raise ValueError
		except ValueError:
			raise ValueError('expected a non-negative integer')

		return num