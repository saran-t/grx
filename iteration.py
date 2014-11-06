import parser
import text
import re
import num

# Produces <before> <content_0> [<content_i> <between>] <content_n> <after>
class IterationBlock(parser.AbstractBlock):

	def __init__(self, counter, content, before = '', between = '', after = '', formatstring = '%s'):
		self.counter = counter
		self.content = content

		self.before = text.blockify(before)
		self.between = text.blockify(between)
		self.after = text.blockify(after)

		self.formatstring = formatstring

	def execute(self):
		output = ''

		output = output + self.before.execute()

		for i in self.counter:
			output = output + (self.formatstring % self.content.execute())

			if self.counter.hasnext():
				output = output + self.between.execute()

		output = output + self.after.execute()
		return output

class IterationCounter(num.AbstractNumber):

	def __init__(self, start, end, stride = 1):
		self.active = False

		self.start = start
		self.end = end

		self.stride = stride

	def numvalue(self):
		return self._value

	def __iter__(self):
		if self.active:
			raise Exception(repr(self) + " this iteration counter is already active")
		else:
			self.active = True
			self._value = self.start.numvalue() - self.stride
			return self

	def hasnext(self):
		return self._value < self.end.numvalue()

	def next(self):
		self._value = self._value + self.stride
		if (self.stride > 0 and self._value <= self.end.numvalue()) or (self.stride < 0 and self._value >= self.end.numvalue()):
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
			start = num.fromstring(m.group(2), context)
		else:
			# no start value, try default
			try:
				start = context.defaultrange[0]
			except AttributeError:
				raise Exception("range start value omitted, but no @defaultrange defined")
		

		if m.group(3) is not None:
			end = num.fromstring(m.group(3), context)
		else:
			# no end value, try default
			try:
				end = context.defaultrange[1]
			except ValueError:
				raise Exception("range end value omitted, but no @defaultrange defined")


		return RangeSpec(name, IterationCounter(start, end))


class RangeSpec(object):
	def __init__(self, name, counter):
		self.name = name
		self.counter = counter
