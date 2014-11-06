import tag
import parser
import text
import num
import d1
from stencil import StencilDefinition

def token_class():
	return D1TagToken


class D1TagToken(tag.TagToken):

	def parse(self, context):

		if len(self.args) != 5:
			raise Exception("@d2 expects exactly 5 arguments")

		else:
			# read derivative operator indices
			try:
				d1indexstring = text.PlainStringContext(self.args[1], context).parse().strip()
				d2indexstring = text.PlainStringContext(self.args[2], context).parse().strip()
			except Exception, e:
				raise Exception("invalid derivative index")

			d1index = num.fromstring(d1indexstring, context)
			d2index = num.fromstring(d1indexstring, context)

			# read d1stencil name
			try:
				d1stencilname = text.PlainStringContext(self.args[3], context).parse().strip()
				d2stencilname = text.PlainStringContext(self.args[4], context).parse().strip()
				
			except Exception, e:
				raise Exception("invalid stencil name")

			d1stencil = context.getvar(d1stencilname)
			if not isinstance(d1stencil, StencilDefinition):
				raise ValueError("'" + d1stencilname + "' is not a @stencil")

			d2stencil = context.getvar(d2stencilname)
			if not isinstance(d2stencil, StencilDefinition):
				raise ValueError("'" + d2stencilname + "' is not a @stencil")

			stencils = [d1stencil, d2stencil]
			dindices = [d1index, d2index]

			inner_context = d1.DerivativeParsingContext(self.args[0], context, dindices)
			(dpointblocks, exprblock) = inner_context.parse()
			return SecondDerivativeBlock(stencils, dindices, dpointblocks, exprblock)

# dindex means the grx variable which holds the index of the coordinate being differentiated with respect to (i.e. the index of the partial differential operator)
# dpointblock means the parser block which holds the string for the current stencil point
# exprblock means the parser block which holds the expression being differentiated

class SecondDerivativeBlock(parser.AbstractBlock):

	def __init__(self, stencils, dindices, dpointblocks, exprblock):
		self.stencils = stencils
		self.dindices = dindices
		self.dpointblocks = dpointblocks
		self.exprblock = exprblock

	def execute(self):
		terms = []

		index1 = self.dindices[0].numvalue()
		index2 = self.dindices[1].numvalue()

		if index1 == index2:
			# diagonal, use second derivative stencil
			for (point, weight) in self.stencils[1]:
				self.dpointblocks[0].content = point
				self.dpointblocks[1].content = point
				terms.append('(%s) * (%s)' % (weight, self.exprblock.execute()))

		else:
			# off-diagonal, double loop over first derivative stencil
			for (point1, weight1) in self.stencils[0]:
				for (point2, weight2) in self.stencils[0]:
					if index1 < index2:
						self.dpointblocks[0].content = point1
						self.dpointblocks[1].content = point2
					else:
						self.dpointblocks[0].content = point2
						self.dpointblocks[1].content = point1

					terms.append('(%s) * (%s) * (%s)' % (weight1, weight2, self.exprblock.execute()))

		from string import join
		return '( ' + join(terms, ' + ') + ' )'
