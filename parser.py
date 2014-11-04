import traceback

iterator_stack = []

def parse(tokens):
	try:
		context = ParsingContext(tokens)
		return context.parse()
	
	except Exception, e:
		print traceback.format_exc()
		token = iterator_stack[-1].current()
		raise Exception('Error: ' + str(token.line) + ':' + str(token.char) + ': ' + str(e.message))
	

class AbstractVariable(object):
	def uniquename(self):
		return '$' + str(id(self))


class AbstractBlock(object):
	pass


class BlockSequence(AbstractBlock):
	
	def __init__(self, blocks):
		self.blocks = blocks

	def execute(self):
		output = ''

		for block in self.blocks:
			output = output + block.execute()

		return output


class ParsingContext(object):

	def __init__(self, tokens, parent = None):
		self.parent = parent
		self._localvars = {}

		if isinstance(tokens, TokenIterator):
			self.tokens_iterator = tokens
		else:
			self.tokens_iterator = TokenIterator(tokens)

	def getvar(self, varname):
		if varname in self._localvars:
			return self._localvars[varname]
		elif self.parent is not None:
			return self.parent.getvar(varname)
		else:
			return None

	def declare(self, varname, varobj):
		if self.getvar(varname) is None:
			self._localvars[varname] = varobj
		else:
			raise Exception(varname + " is already declared in this context")

	def __getattribute__(self, name):
		try:
			return object.__getattribute__(self, name)
		except AttributeError, e:
			if self.parent is not None:
				return self.parent.__getattribute__(name)
			else:
				raise e

	def __iter__(self):
		return self.tokens_iterator

	def append_block(self, block):
		self._blocks.append(block)


	def parse(self):
		self.tokens_iterator.start()
		return_value = self.parse_all()
		self.tokens_iterator.stop()
		return return_value

	def parse_all(self):
		self._blocks = []

		for token in self.tokens_iterator:
			try:
				block = self.parse_token(token)
				if block is not None:
					self._blocks.append(block)
			except LeaveContext:
				break

		return BlockSequence(self._blocks)

	def parse_token(self, token):
		return token.parse(self)


class TokenIterator(object):

	def __init__(self, tokens):
		self._tokens = tokens
		self.start_count = 0
	
	def __iter__(self):
		return self

	def current(self):
		return self._tokens[self._index - 1]

	def start(self):
		if self.start_count == 0:
			self._index = 0
			iterator_stack.append(self)
		self.start_count = self.start_count + 1

	def stop(self):
		self.start_count = self.start_count - 1
		if self.start_count == 0:
			iterator_stack.pop()
			self._index = len(self._tokens)

	def next(self):
		if iterator_stack[-1] is not self:
			raise Exception('cannot advance the TokenIterator which is not currently on top of iterator_stack')
		if self._index < len(self._tokens):
			token = self._tokens[self._index]
			self._index = self._index + 1
			return token
		else:
			raise StopIteration


class LeaveContext(Exception):
	pass

