import tag
import parser
import text
import arrayexpand
import num
from stencil import StencilDefinition

def token_class():
	return D1TagToken


class D1TagToken(tag.TagToken):

	def parse(self, context):

		if len(self.args) != 3:
			raise Exception("@d1 expects exactly 3 arguments")

		else:

			# read derivative operator index
			try:
				d1indexstring = text.PlainStringContext(self.args[1], context).parse().strip()
			except Exception, e:
				raise Exception("invalid derivative index")

			d1index = num.fromstring(d1indexstring, context)

			# read stencil name
			try:
				d1stencilname = text.PlainStringContext(self.args[2], context).parse().strip()
			except Exception, e:
				raise Exception("invalid stencil name")

			d1stencil = context.getvar(d1stencilname)
			if not isinstance(d1stencil, StencilDefinition):
				raise ValueError("'" + d1stencilname + "' is not a @stencil")

			
			stencils = [d1stencil]
			dindices = [d1index]

			inner_context = DerivativeParsingContext(self.args[0], context, dindices)
			(dpointblocks, exprblock) = inner_context.parse()
			return FirstDerivativeBlock(stencils, dindices, dpointblocks, exprblock)


# dindex means the grx variable which holds the index of the coordinate being differentiated with respect to (i.e. the index of the partial differential operator)
# dpointblock means the parser block which holds the string for the current stencil point
# exprblock means the parser block which holds the expression being differentiated

class FirstDerivativeBlock(parser.AbstractBlock):

	def __init__(self, stencils, dindices, dpointblocks, exprblock):
		self.stencil = stencils[0]
		# self.dindices = We don't need to inspect dindices for first derivative
		self.dpointblock = dpointblocks[0]
		self.exprblock = exprblock

	def execute(self):
		terms = []
		for (point, weight) in self.stencil:
			self.dpointblock.content = point
			terms.append('(%s) * (%s)' % (weight, self.exprblock.execute()))

		from string import join
		return '( ' + join(terms, ' + ') + ' )'


class DerivativeParsingContext(parser.ParsingContext):

	def __init__(self, tokens, context, dindices):
		parser.ParsingContext.__init__(self, tokens, context)
		self.dindices = dindices
		self.dpointblocks = [text.TextBlock('') for dindex in dindices]

	def parse_all(self):
		return (self.dpointblocks, parser.ParsingContext.parse_all(self))

	def parse_token(self, token):
		if isinstance(token, arrayexpand.ArrayExpandToken):
			iterblock = token.parse(self);
			rawcontent = iterblock.content
			deltablock = DerivativeDeltaBlock(iterblock.counter, self.dindices, self.dpointblocks)
			iterblock.content = parser.BlockSequence([rawcontent, deltablock])
			return iterblock
		else:
			return parser.ParsingContext.parse_token(self, token)


class DerivativeDeltaBlock(parser.AbstractBlock):

	def __init__(self, index_counter, dindices, dpointblocks):
		self.index_counter = index_counter
		self.dindices = dindices
		self.dpointblocks = dpointblocks

	def execute(self):
		from itertools import izip
		for (dindex, dpointblock) in izip(self.dindices, self.dpointblocks):
			if self.index_counter.numvalue() == dindex.numvalue():
				# TODO: fix this temporary hack!
				rawstring = dpointblock.execute()
				from string import join
				return ' + (' + join(rawstring.split('#'), self.index_counter.execute()) + ')'
				# end hack

		return ''

