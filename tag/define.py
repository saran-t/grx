import tag
import parser
import iteration
import definescope
import substitution

def token_class():
	return DefineTagToken


class DefineTagToken(tag.TagToken):

	def parse(self, context):
		if len(self.args) != 2:
			raise Exception("@define expects exactly two arguments")
			
		else:
			try:
				env = context._defineenv
			except AttributeError:
				raise Exception("cannot use @define outside of a @definescope")

			matchblock = parser.ParsingContext(self.args[0], context).parse()
			replaceblock = parser.ParsingContext(self.args[1], context).parse()
			return substitution.DefinitionBlock(env, matchblock, replaceblock)	
			

class DefineScopeContext(tag.ExtendedTagContext):

	def __init__(self, tokens, parent, tag):
		tag.ExtendedTagContext.__init__(self, tokens, parent, tag)
		self.env = substitution.SubstitutionEnvironment()
