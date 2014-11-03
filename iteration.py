import parser
import text
import re

# Produces <before> <content_0> [<content_i> <between>] <content_n> <after>
class IterationBlock(parser.AbstractBlock):

	def __init__(self, counter, content, before = '', between = '', after = ''):
		self.counter = counter
		self.content = content

		self.before = text.blockify(before)
		self.between = text.blockify(between)
		self.after = text.blockify(after)

	def execute(self):
		output = ''

		output = output + self.before.execute()

		for i in self.counter:
			output = output + self.content.execute()

			if self.counter.hasnext():
				output = output + self.between.execute()

		output = output + self.after.execute()
		return output


class IterationConstant(parser.AbstractVariable):

	singletons = {}

	def __init__(self, value):
		self._value = value;

	@staticmethod	
	def get(value):
		value_int = int(value)
		if value_int < 0:
			raise ValueError

		if not (value_int in IterationConstant.singletons):
			IterationConstant.singletons[value_int] = IterationConstant(value_int)

		return IterationConstant.singletons[value_int]

	def value(self):
		return self._value

	def execute(self):
		return str(self._value)


class IterationCounter(parser.AbstractVariable):

	def __init__(self, start, end):
		self.active = False

		if isinstance(start, parser.AbstractVariable):
			self._start = start
		else:
			self._start = IterationConstant.get(start)

		if isinstance(end, parser.AbstractVariable):
			self._end = end
		else:
			self._end = IterationConstant.get(end)

	def value(self):
		return self._value

	def __iter__(self):
		if self.active:
			raise Exception(repr(self) + " this iteration counter is already active")
		else:
			self.active = True
			self._value = self._start.value() - 1
			return self

	def hasnext(self):
		return self._value < self._end.value()

	def next(self):
		self._value = self._value + 1
		if self._value <= self._end.value():
			return self._value
		else:
			self.active = False
			raise StopIteration

	def execute(self):
		return str(self._value)


class RangeSpecContext(text.PlainStringContext):

	range_regex = re.compile(r"\s*([a-zA-Z_]\w*)\s*(?:\s*=\s*(\w+)?\s*\.\.\s*(\w+)?)?")

	def parse_all(context):

		try:
			rangestring = text.PlainStringContext.parse_all(context)
			m = RangeSpecContext.range_regex.match(rangestring)
			if (m is None) or (m.group(0) != rangestring):
				raise ValueError

		except Exception:
			raise ValueError("invalid range specification")


		name = m.group(1)

		if m.group(2) is not None:
			# try interpreting as a variable name first
			start = context.getvar(m.group(2))
			if start is None:
				# failing that try it as an integer literal
				try:
					start = IterationConstant.get(m.group(2))
				except ValueError:
					raise Exception("'" + m.group(2) + "' is not declared in this context")
		else:
			# no start value, try default
			try:
				start = IterationConstant.get(context.defaultrange[0])
			except ValueError:
				raise Exception("start value omitted, but no @defaultrange defined")
		

		if m.group(3) is not None:
			# try interpreting as a variable name first
			end = context.getvar(m.group(3))
			if end is None:
				# failing that try it as an integer literal
				try:
					end = IterationConstant.get(m.group(3))
				except ValueError:
					raise Exception("'" + m.group(3) + "' is not declared in this context")
		else:
			# no end value, try default
			try:
				end = IterationConstant.get(context.defaultrange[1])
			except ValueError:
				raise Exception("end value omitted, but no @defaultrange defined")


		return RangeSpec(name, IterationCounter(start, end))


class RangeSpec(object):
	def __init__(self, name, counter):
		self.name = name
		self.counter = counter
