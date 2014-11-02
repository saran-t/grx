import re

def lex(string):
	lexer = Lexer(string, start_line = 1, start_char = 1)
	return lexer.lex()

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
		print repr(self.line) + ':' + repr(self.char) + ':\t' + prefix + ' @' + self.name
		prefix = prefix + '>>>>'
		for arg in self.args:
			print repr(arg[0].line) + ':' + repr(arg[0].char) + ':\t' + prefix + ' [[ TagArg ]]'
			for token in arg:
				token.print_debug(prefix + '>>>>')

	def __repr__(self):
		return '<@' + self.name + '[' + repr(self.args) + ']>'


class Lexer(object):

	class State(object):
		TEXT = 0
		TAG = 1
		ARRAYEXPAND = 2

	def __init__(self, string, start_line, start_char):
		self.string = string
		self.start_line = start_line
		self.start_char = start_char


	def reset(self):
		self.chars_read = 0
		self.state = Lexer.State.TEXT
		self.tokens = []

		self.char = ''
		self.line_number = self.start_line
		self.char_pos = self.start_char
		self.advance()


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


	def append_token(self, token):
		self.tokens.append(token)


	def lex(lexer):
		lexer.reset()
		while lexer.char is not None:
			if lexer.state == Lexer.State.TEXT:
				lexer.lex_text()
			elif lexer.state == Lexer.State.ARRAYEXPAND:
				lexer.lex_arrayexpand()
			elif lexer.state == Lexer.State.TAG:
				lexer.lex_tag()
		return TokensSequence(lexer.tokens)


	# Lex an inert blob of text
	def lex_text(lexer):

		string = ''

		start_line = lexer.line_number
		start_char = lexer.char_pos

		class InnerState(object):
			READ = 0
			OPENBRACKET_WAIT = 1
			DONE = 2

		inner_state = InnerState.READ

		while (inner_state != InnerState.DONE) and (lexer.char is not None):

			if inner_state == InnerState.READ:

				if lexer.char == '[':
					inner_state = InnerState.OPENBRACKET_WAIT
				elif lexer.char == '@':
					inner_state = InnerState.DONE
					lexer.state = Lexer.State.TAG
				else:
					string = string + lexer.char

			elif inner_state == InnerState.OPENBRACKET_WAIT:

				if lexer.char == '[':
					inner_state = InnerState.DONE
					lexer.state = Lexer.State.ARRAYEXPAND
				elif lexer.char == '@':
					string = string + '['
					inner_state = InnerState.DONE
					lexer.state = Lexer.State.TAG
				else:
					string = string + '[' + lexer.char
					inner_state = InnerState.READ
			
			lexer.advance()

		if len(string) > 0:
			lexer.append_token(TextToken(start_line, start_char, string))


	# Lex an array expansion directive
	def lex_arrayexpand(lexer):

		string = ''

		line_number = lexer.line_number
		char_pos = lexer.char_pos

		class InnerState(object):
			READ = 0
			OPENBRACKET_WAIT = 1
			CLOSEBRACKET_WAIT = 2
			DONE = 3

		inner_state = InnerState.READ
		opencount = 0

		while (inner_state != InnerState.DONE):

			if lexer.char is None:
				raise Exception('Error: ' + str(line_number) + ':' + str(char_pos - 2) + ': missing a closing ]]')

			if inner_state == InnerState.READ:

				if lexer.char == '[':
					inner_state = InnerState.OPENBRACKET_WAIT
				elif lexer.char == ']':
					inner_state = InnerState.CLOSEBRACKET_WAIT
				else:
					string = string + lexer.char

			elif inner_state == InnerState.OPENBRACKET_WAIT:

				if lexer.char == '[':
					opencount = opencount + 1

				string = string + '[' + lexer.char
				inner_state = InnerState.READ

			elif inner_state == InnerState.CLOSEBRACKET_WAIT:

				if lexer.char == ']':
					if opencount > 0:
						string = string + ']]'
						opencount = opencount - 1
					else:
						inner_state = InnerState.DONE
				else:
					string = string + ']' + lexer.char
					inner_state = InnerState.READ

			lexer.advance()
		
		# Process the expansion string as if it were a separate GRX document
		inner_tokens = Lexer(string, start_line = line_number, start_char = char_pos).lex()
		lexer.append_token(ArrayExpandToken(line_number, char_pos - 2, inner_tokens))
		lexer.state = Lexer.State.TEXT


	# Lex an @tag
	def lex_tag(lexer):

		name = ''
		args = []

		line_number = lexer.line_number
		char_pos = lexer.char_pos

		class InnerState(object):
			READ = 0
			OPENBRACKET_WAIT = 1
			DONE = 2

		inner_state = InnerState.READ

		# Match only [a-zA-Z0-9_] for a tag name
		tagname = re.compile(r"\w")

		while (inner_state != InnerState.DONE) and (lexer.char is not None):

			if inner_state == InnerState.READ:
				if tagname.match(lexer.char):
					name = name + lexer.char
					lexer.advance()
				elif lexer.char == '[':
					inner_state = InnerState.OPENBRACKET_WAIT
					lexer.advance()
				else:
					inner_state = InnerState.DONE

			elif inner_state == InnerState.OPENBRACKET_WAIT:
				if lexer.char == '[':
					args = lexer.advance().lex_tag_args()
					inner_state = InnerState.DONE
				else:
					# This should be safe here. But don't try this elsewhere!
					lexer.char = '['
					lexer.chars_read = lexer.chars_read - 1
					lexer.char_pos = lexer.char_pos - 1

					inner_state = InnerState.DONE
			
		lexer.append_token(TagToken(line_number, char_pos - 1, name, args))
		lexer.state = Lexer.State.TEXT


	# Lex arguments list for an @tag
	def lex_tag_args(lexer):

		args = []

		string = ''
		opencount = 0

		start_line = lexer.line_number
		start_char = lexer.char_pos

		arg_line = lexer.line_number
		arg_char = lexer.char_pos

		class InnerState(object):
			READ = 0
			OPENBRACKET_WAIT = 1
			CLOSEBRACKET_WAIT = 2
			DONE = 3

		inner_state = InnerState.READ

		while (inner_state != InnerState.DONE):

			if not lexer.char:
				raise Exception('Error: ' + str(start_line) + ':' + str(start_char - 1) + ': @tag argument list is missing a closing ]')

			param_fully_read = False

			if inner_state == InnerState.READ:

				if lexer.char == '[':
					inner_state = InnerState.OPENBRACKET_WAIT
				elif lexer.char == ']':
					inner_state = InnerState.CLOSEBRACKET_WAIT
				elif (lexer.char == ',') and (opencount == 0):
					param_fully_read = True
				else:
					string = string + lexer.char

			elif inner_state == InnerState.OPENBRACKET_WAIT:

				if lexer.char == '[':
					opencount = opencount + 1
				
				string = string + '[' + lexer.char
				inner_state = InnerState.READ

			elif inner_state == InnerState.CLOSEBRACKET_WAIT:

				if lexer.char == ']':
					if opencount > 0:
						opencount = opencount - 1
						string = string + ']]'
						inner_state = InnerState.READ
					else:
						param_fully_read = True
						inner_state = InnerState.DONE
				else:
					string = string + ']' + lexer.char
					inner_state = InnerState.READ

			if param_fully_read:

				# Process each complete argument string as if it were a separate GRX document
				inner_tokens = Lexer(string, start_line = arg_line, start_char = arg_char).lex()
				args.append(inner_tokens)
				
				# Start a new argument string
				string = ''
				lexer.advance()
				arg_line = lexer.line_number
				arg_char = lexer.char_pos

			else:
				# Keep reading into the current argument string
				lexer.advance()

		return args

