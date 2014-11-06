import parser
import text
import tag

def token_class():
	return StencilTagToken


class StencilTagToken(tag.TagToken):
	def parse(self, context):
		
		if len(self.args) != 1:
			raise Exception("@stencil expects exactly one argument")
		else:
			try:
				stencil_name = text.PlainStringContext(self.args[0], context).parse()
				m = parser.valid_varname.match(stencil_name)
				if (not m) or (m.group(0) != stencil_name):
					raise ValueError
			except Exception, e:
				raise ValueError("invalid stencil name")
		
		inner_context = StencilContext(iter(context), context)
		stencil_def = inner_context.parse()
		context.declare(stencil_name, stencil_def)


class StencilDefinition(parser.AbstractVariable):

	def __init__(self, points, weights):
		if len(points) != len(weights):
			raise Exception("@points and @weights should have an equal number of arguments")
		else:
			self.points = points
			self.weights = weights
			self._len = len(self.points)

	def __len__(self):
		return self._len

	def __iter__(self):
		from itertools import izip
		return izip(self.points, self.weights)


class StencilContext(parser.ParsingContext):

	def __init__(self, *args, **kwargs):
		parser.ParsingContext.__init__(self, *args, **kwargs)
		self.points = None
		self.weights = None

	def parse_all(self):
		parser.ParsingContext.parse_all(self)

		if not self.points:
			raise Exception("@points not defined for this @stencil")

		elif not self.weights:
			raise Exception("@weights not defined for this @stencil")

		else:
			return StencilDefinition(self.points, self.weights)

	def parse_token(self, token):
		import arrayexpand
		if isinstance(token, tag.TagToken):

			if token.name == 'points':
				self.points = self.parse_args(token.args)

			elif token.name == 'weights':
				self.weights = self.parse_args(token.args)

			elif token.name == 'end':
				raise parser.LeaveContext

			else:
				raise Exception("unexpected tag @" + token.name + " inside @stencil")

		elif isinstance(token, text.TextToken) and len(token.text.strip()) > 0:
			raise Exception("unexpected string inside @stencil")

		elif isinstance(token, arrayexpand.ArrayExpandToken):
			raise Exception("array expansion cannot be used inside @stencil")

	def parse_args(self, args):
		parsed_args = []
		for arg in args:
			parsed_args.append(text.PlainStringContext(arg, self).parse().strip())
		return parsed_args			
