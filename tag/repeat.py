import tag
import iteration

def token_class():
	return RepeatTagToken


class AbstractRepeatTagToken(tag.TagToken):

	def parse(self, context):
		counters = []
	
		for arg in self.args:
			rangespec = iteration.RangeSpecContext(arg, context).parse()
			context.declare(rangespec.name, rangespec.counter)
			counters.append(rangespec.counter)
	
		inner_context = tag.ExtendedTagContext(iter(context), context)
		content = inner_context.parse()

		return (counters, content)


class RepeatTagToken(AbstractRepeatTagToken):

	def parse(self, context):
	
		(counters, content) = AbstractRepeatTagToken.parse(self, context)
		
		#  we put this here since we still need to process the inner content up to @end even for an empty range!
		if len(counters) == 0:
			return
		
		block = content
		for counter in reversed(counters):
			block = iteration.IterationBlock(counter, block)
		
		context.append_block(block)
