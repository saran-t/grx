import re

class Tokens(object):
	def __init__(self, tokens):
		self.tokens = tokens

	def print_debug(self):
		for i in self:
			print i

	def __iter__(self):
		return iter(self.tokens)

class TextToken(object):
	def __init__(self, string, line, char):
		self.text = string
		self.line = line
		self.char = char

	def __repr__(self):
		return repr(self.line) + ':' + repr(self.char) + ':\t' + self.text

class TagToken(object):
	def __init__(self, string, line, char):
		self.name = string
		self.line = line
		self.char = char

	def __repr__(self):
		return repr(self.line) + ':' + repr(self.char) + ':\t' + '@' + self.name

class ParamToken(object):
	def __init__(self, string, line, char):
		self.text = string
		self.line = line
		self.char = char

	def __repr__(self):
		return repr(self.line) + ':' + repr(self.char) + ':\t' + '[' + self.text + ']'

def lex(string):

	tokens = []

	# Matches one line, works with either Windows or UNIX linebreak
	readline = re.compile(r"([^\r\n]*)(\r\n|\n)?")

	line_number = 1

	while len(string) > 0:

		# Read a single line from the string and pass it to the line lexer
		m = readline.match(string)
		if m is not None:
			tokens = tokens + lex_line(m.group(1), line_number)
			string = string[m.end(0):]
			line_number = line_number + 1
		else:
			raise Exception("GRX lexer failed unexpectedly")


	return Tokens(tokens)

def lex_line(line, line_number):

	# Treat empty line as a special case, makes life easier later on
	if len(line) == 0:
		return [TextToken('', line_number, 1)]

	tokens = []

	# Matches longest string up to either an @ character or a [[
	text_regex = re.compile(r"[^\@|(\[\[)]+")

	# Matches longest string of alphanumeric and underscore following an @ character
	tag_regex = re.compile(r"\@(\w*)")

	# Matches the longest string between a pair of [___]
	params_regex = re.compile(r"\[([^\[\]]*)\]")

	char_pos = 1

	while len(line) > 0:
		matched = False

		# Tokenize a blob of inert text
		m = text_regex.match(line)
		if m is not None:
			matched = True
			tokens.append(TextToken(m.group(0), line_number, m.start(0) + char_pos))
			line = line[m.end(0):]
			char_pos = char_pos + m.end(0)

		# Tokenize an @tag
		m = tag_regex.match(line)
		if m is not None:
			matched = True
			tokens.append(TagToken(m.group(1), line_number, m.start(0) + char_pos))
			line = line[m.end(0):]
			char_pos = char_pos + m.end(0)

			# Tokenize a parameter list immediately following an @tag
			m = params_regex.match(line)
			if m is not None:
				tokens = tokens + lex_params(m.group(1), line_number, m.start(1) + char_pos)
				line = line[m.end(0):]
				char_pos = char_pos + m.end(0)

		if matched == False:
			# If this ever happens then go fix our regex -- definitely a bug
			raise Exception("GRX lexer failed unexpectedly in the middle of a line")

	return tokens

def lex_params(params, line_number, char_pos):
	
	tokens = []

	separator_regex = re.compile(r"\s*,\s*")
	orig_len = len(params)
	params = params.lstrip()
	char_pos = char_pos + (orig_len - len(params))

	while params is not None:
		m = separator_regex.search(params)
		if m is not None:
			tokens.append(ParamToken(params[0:m.start(0)], line_number, char_pos))
			params = params[m.end(0):]
			char_pos = char_pos + m.end(0)
		else:
			tokens.append(ParamToken(params.rstrip(), line_number, char_pos))
			params = None

	return tokens