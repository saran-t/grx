import tag
import expand
import iteration

def token_class():
	return RExpandTagToken


'''
@rexpand is like @expand but the number runs backwards
'''
class RExpandTagToken(tag.TagToken, expand.AbstractExpandToken):

	def __init__(self, *args, **kwargs):
		tag.TagToken.__init__(self, *args, **kwargs)
	
	# Don't split args at commas
	@staticmethod
	def _lexer_split_args():
		return False

	def parse(self, context):

		if len(self.args) != 1:
			raise Exception("@rexpand expects exactly one argument")
		else:
			self.content = self.args[0]

		(counter, content) = expand.AbstractExpandToken.parse(self, context)
		(counter.start, counter.end, counter.stride) = (counter.end, counter.start, -1)

		return iteration.IterationBlock(counter, content)