import tag
import iteration

def token_class():
	return IterateTagToken

'''
Represents general iterator tags (e.g. @iterate, @sum)
'''
class AbstractIteratorToken(tag.TagToken):

	'''
	General parsing logic for iteration-type tags
	Return the range specifications and contents to be decorated by specific tags
	'''
	def parse(self, context):

		inner_context = tag.ExtendedTagContext(iter(context), context, self)

		counters = []
	
		for arg in self.args:
			rangespec = iteration.RangeSpecContext(arg, inner_context).parse()
			inner_context.declare(rangespec.name, rangespec.counter)
			counters.append(rangespec.counter)
		
		content = inner_context.parse()

		return (counters, content)


'''
@iterate is a straightforward iterator tag that just repeats its content while incrementing the counter
'''
class IterateTagToken(AbstractIteratorToken):

	'''
	Takes the output from AbstractExpansionToken and stick it straight into an IterationBlock
	'''
	def parse(self, context):
	
		(counters, content) = AbstractIteratorToken.parse(self, context)
		
		#  we put this here since we still need to process the inner content up to @end even for an empty range!
		if len(counters) == 0:
			return
		
		block = content
		for counter in reversed(counters):
			block = iteration.IterationBlock(counter, block)

		return block
