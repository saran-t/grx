import parser

class Mode:
	REPLACE = 1
	PRAGMA = 2

class SubstitutionBlock(parser.AbstractBlock):

	def __init__(self, env, content):
		self.env = env
		self.content = content
		
	def execute(self):
		if self.env.mode == Mode.REPLACE:
			return self.env.replace(self.content.execute())
		elif self.env.mode == Mode.PRAGMA:
			return self.content.execute() + self.env.undef_string()


class DefinitionBlock(parser.AbstractBlock):

	def __init__(self, env, matchblock, replaceblock):
		self.env = env
		self.matchblock = matchblock
		self.replaceblock = replaceblock

	def execute(self):
		(match, replace) = self.env.define(self.matchblock.execute(), self.replaceblock.execute())

		if self.env.mode == Mode.REPLACE:
			return ''
		elif self.env.mode == Mode.PRAGMA:
			if match and replace:
				return '#define ' + match + ' ' + replace
			else:
				return ''


class SubstitutionEnvironment(object):

	max_iteration = 10

	def __init__(self, mode = Mode.REPLACE):
		self.dict = {}
		if not (mode == Mode.REPLACE or mode == Mode.PRAGMA):
			raise ValueError("invalid mode for SubstitutionEnvironment")
		else:
			self.mode = mode


	def define(self, rawmatch, rawreplace):
		match = rawmatch.strip()
		replace = rawreplace.strip()

		if match == replace:
			return (None, None)

		elif match in self.dict and self.dict[match] != replace:
			raise Exception(match + ' has already been @defined')
		
		else:
			self.dict[match] = replace
			return (match, replace)


	def undef_string(self):
		string = ''
		for match in self.dict:
			string = string + '#undef ' + match + '\n'
		return string


	def replace(self, string):
		done = False
		oldstring = string
		newstring = string
		iterations = 0

		while not done and iterations < SubstitutionEnvironment.max_iteration:
			for match in self.dict:
				newstring = newstring.replace(match, self.dict[match])

			done = (newstring == oldstring)
			oldstring = newstring
			iterations = iterations + 1

		if not done:
			raise Exception("SubstitutionEnvironment has not converged after " + str(SubstitutionEnvironment.max_iteration) + ' attempts, suspect circular @defines')
		else:
			return newstring


	