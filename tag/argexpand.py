import tag
import expand
import iteration

def token_class():
	return ArgExpandTagToken


'''
@rexpand is like @expand but the number runs backwards
'''
class ArgExpandTagToken(tag.TagToken, expand.AbstractExpandToken):

	def __init__(self, *args, **kwargs):
		tag.TagToken.__init__(self, *args, **kwargs)
	
	# Don't split args at commas
	@staticmethod
	def _lexer_split_args():
		return False

	def parse(self, context):

		if len(self.args) != 1:
			raise Exception("@argexpand expects exactly one argument")
		else:
			self._rawcontent = self.args[0]

		(counter, content) = expand.AbstractExpandToken.parse(self, context)
		return iteration.IterationBlock(counter, content, between = ',')