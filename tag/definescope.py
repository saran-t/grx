import tag
import iteration
import substitution

def token_class():
	return DefineScopeTagToken


class DefineScopeTagToken(tag.TagToken):

	def parse(self, context):
		inner_context = DefineScopeContext(iter(context), context, self)
		content = inner_context.parse()
		return substitution.SubstitutionBlock(inner_context._defineenv, content)


class DefineScopeContext(tag.ExtendedTagContext):

	def __init__(self, tokens, parent, tagtoken):
		tag.ExtendedTagContext.__init__(self, tokens, parent, tagtoken)
		self._defineenv = substitution.SubstitutionEnvironment(substitution.Mode.PRAGMA)
