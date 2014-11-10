import tag
import text
import num

def token_class():
	return DefaultRangeTagToken


class DefaultRangeTagToken(tag.TagToken):
	def parse(self, context):
		if len(self.args) != 2:
			raise ValueError("@defaultrange takes exactly two arguments")

		minval = text.PlainStringContext(self.args[0], context).parse()
		maxval = text.PlainStringContext(self.args[1], context).parse()

		minvar = num.ConstantNumber.getinstance(minval)
		maxvar = num.ConstantNumber.getinstance(maxval)

		context.declare('RANGEMIN', minvar)
		context.declare('RANGEMAX', maxvar)
		context.defaultrange = [minvar, maxvar]
