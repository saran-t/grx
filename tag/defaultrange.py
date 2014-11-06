import tag
import text
import num

def token_class():
	return DefaultRangeTagToken


class DefaultRangeTagToken(tag.TagToken):
	def parse(self, context):
		if len(self.args) != 2:
			raise ValueError("@defaultrange takes exactly two arguments")

		start = text.PlainStringContext(self.args[0], context).parse()
		end = text.PlainStringContext(self.args[1], context).parse()

		context.defaultrange = [num.ConstantNumber.getinstance(start), num.ConstantNumber.getinstance(end)]
