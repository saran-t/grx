import re

class TokensSequence(object):
	def __init__(self, tokens):
		self.tokens = tokens

	def print_debug(self):
		for token in self:
			token.print_debug()

	def __iter__(self):
		return iter(self.tokens)

	def __getitem__(self, key):
		return self.tokens[key]

	def __contains__(self, item):
		return (item in self.tokens)

	def __len__(self):
		return len(self.tokens)

	def __repr__(self):
		return 'TokensSequence' + repr(self.tokens)

class TextToken(object):
	def __init__(self, line, char, text):
		self.line = line
		self.char = char
		self.text = text

	def print_debug(self, prefix = ''):
		print repr(self.line) + ':' + repr(self.char) + ':\t' + prefix + ' ' + self.text

	def __repr__(self):
		return '<TextToken>'


class ArrayExpandToken(object):
	def __init__(self, line, char, inner_tokens):
		self.line = line
		self.char = char
		self.inner_tokens = inner_tokens

	def print_debug(self, prefix = ''):
		print repr(self.line) + ':' + repr(self.char) + ':\t' + prefix + ' [[ ArrayExpand ]]'
		for token in self.inner_tokens:
			token.print_debug(prefix + '>>>>')

	def __repr__(self):
		return '<[[' + repr(self.inner_tokens) + ']]>'


class TagToken(object):
	def __init__(self, line, char, name, args = []):
		self.line = line
		self.char = char
		self.name = name
		self.args = args

	def print_debug(self, prefix = ''):
		print repr(self.line) + ':' + repr(self.char) + ':\t' + prefix + '@' + self.name
		prefix = prefix + '>>>>'
		for arg in self.args:
			print repr(arg[0].line) + ':' + repr(arg[0].char) + ':\t' + prefix + ' [ TagArg ]'
			for token in arg:
				token.print_debug(prefix + '>>>>')

	def __repr__(self):
		return '<@' + self.name + repr(self.args) + '>'


class LexerState(object):
	TEXT = 0
	TAG = 1
	ARRAYEXPAND = 2

class Lexer(object):
	def __init__(self, string, start_line = 1, start_char = 1):
		self.string = string
		self.chars_read = 0

		self.state = LexerState.TEXT
		self.tokens = []

		self.char = ''
		self.line_number = start_line
		self.char_pos = start_char

		self.advance()

	def append_token(self, token):
		self.tokens.append(token)

	def get_tokens(self):
		if len(self.tokens) == 0:
			return None
		elif len(self.tokens) == 1:
			return self.tokens[0]
		else:
			return TokensSequence(self.tokens)

	def advance(self):
		if self.chars_read < len(self.string):
			if self.char == '\n':
				self.line_number = self.line_number + 1
				self.char_pos = 1
			elif self.char != '':
				self.char_pos = self.char_pos + 1

			self.char = self.string[self.chars_read]
			self.chars_read = self.chars_read + 1

		else:
			self.char = None

		return self


def lex(string, start_line = 1, start_char = 1):

	lexer = Lexer(string, start_line, start_char)

	while lexer.char is not None:
		if lexer.state == LexerState.TEXT:
			lex_text(lexer)
		elif lexer.state == LexerState.ARRAYEXPAND:
			lex_arrayexpand(lexer)
		elif lexer.state == LexerState.TAG:
			lex_tag(lexer)

	return lexer.get_tokens()


# Lex an inert blob of text
def lex_text(lexer):

	text = ''

	start_line = lexer.line_number
	start_char = lexer.char_pos

	class InnerState(object):
		TEXT = 0
		ARRAYEXPAND_WAIT = 1

	inner_state = InnerState.TEXT

	while (lexer.state == LexerState.TEXT) and (lexer.char is not None):

		if lexer.char == '@':
			lexer.state = LexerState.TAG

		elif lexer.char == '[':
			if inner_state == InnerState.ARRAYEXPAND_WAIT:
				lexer.state = LexerState.ARRAYEXPAND
			else:
				inner_state = InnerState.ARRAYEXPAND_WAIT
				
		else:
			if inner_state == InnerState.ARRAYEXPAND_WAIT:
				text = text + '[' + lexer.char
				inner_state = InnerState.TEXT
			else:
				text = text + lexer.char
		
		lexer.advance()


	if len(text) > 0:
		lexer.append_token(TextToken(start_line, start_char, text))

# Lex an array expansion directive
def lex_arrayexpand(lexer):

	text = ''

	line_number = lexer.line_number
	char_pos = lexer.char_pos

	class InnerState(object):
		READ = 0
		CLOSE_WAIT = 1

	inner_state = InnerState.READ
	opencount = 0

	while (lexer.state == LexerState.ARRAYEXPAND):

		if lexer.char is None:
			raise Exception('Error: ' + str(line_number) + ':' + str(char_pos - 2) + ': missing a closing ]]')

		if lexer.char == '[':
			text = text + lexer.char
			opencount = opencount + 1

		elif lexer.char == ']':
			if opencount > 0:
				text = text + lexer.char
				opencount = opencount - 1
			elif inner_state == InnerState.CLOSE_WAIT:
				lexer.state = LexerState.TEXT
			else:
				inner_state = InnerState.CLOSE_WAIT

		else:
			if inner_state == InnerState.CLOSE_WAIT:
				text = text + ']' + lexer.char
				inner_state = InnerState.READ
			else:
				text = text + lexer.char

		lexer.advance()
	
	# Process the expansion string as if it were a separate GRX document
	inner_tokens = lex(text, line_number, char_pos)
	lexer.append_token(ArrayExpandToken(line_number, char_pos - 2, inner_tokens))


# Lex an @tag
def lex_tag(lexer):

	name = ''
	args = []

	line_number = lexer.line_number
	char_pos = lexer.char_pos

	# Match only [a-zA-Z0-9_] for a tag name
	tagname = re.compile(r"\w")

	while (lexer.state == LexerState.TAG) and (lexer.char is not None):

		if tagname.match(lexer.char) is not None:
			name = name + lexer.char
			lexer.advance()
		
		else:
			if lexer.char == '[':
				args = lex_tag_args(lexer.advance())

			lexer.state = LexerState.TEXT
		
	lexer.append_token(TagToken(line_number, char_pos - 1, name, args))


# Lex arguments list for an @tag
def lex_tag_args(lexer):

	args = []

	string = ''
	opencount = 0

	start_line = lexer.line_number
	start_char = lexer.char_pos

	arg_line = lexer.line_number
	arg_char = lexer.char_pos

	while opencount >= 0:

		if lexer.char is None:
			raise Exception('Error: ' + str(start_line) + ':' + str(start_char - 1) + ': @tag argument list is missing a closing ]')

		param_fully_read = False

		# Need this to handle nested [...] inside our arguments list
		if lexer.char == '[':
			opencount = opencount + 1

		elif lexer.char == ']':
			if opencount == 0:
				# Genuine end of arguments list, treat whatever string we have in the buffer as the last argument
				param_fully_read = True

			opencount = opencount - 1

		# Commas appearing inside inner brackets are NOT argument delimiters!
		elif (lexer.char == ',') and (opencount == 0):
			param_fully_read = True

		if param_fully_read:

			# Process each complete argument string as if it were a separate GRX document
			inner_tokens = lex(string, arg_line, arg_char)
			args.append(inner_tokens)
			
			# Start a new argument string
			string = ''
			lexer.advance()
			arg_line = lexer.line_number
			arg_char = lexer.char_pos

		else:
			# Keep reading into the current argument string
			string = string + lexer.char
			lexer.advance()

	return args