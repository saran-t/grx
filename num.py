import parser

class AbstractNumber(parser.AbstractVariable):
	pass


class ConstantNumber(AbstractNumber):

	singletons = {}

	def __init__(self, value):
		self._value = value;

	@staticmethod	
	def getinstance(value):
		value_int = int(value)
		if value_int < 0:
			raise ValueError

		if not (value_int in ConstantNumber.singletons):
			ConstantNumber.singletons[value_int] = ConstantNumber(value_int)

		return ConstantNumber.singletons[value_int]

	def numvalue(self):
		return self._value

	def execute(self):
		return str(self._value)


def fromstring(string, context):
	string = string.strip()

	# try interpreting as a variable name first
	num = context.getvar(string)

	if num is None:
		# failing that try it as an integer literal
		try:
			num = ConstantNumber.getinstance(string)
		except ValueError:
			raise Exception("'" + string + "' does not represent a numerical value")

	return num