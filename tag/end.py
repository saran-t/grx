import tag
import parser
import text

def token_class():
	return EndTagToken

class EndTagToken(tag.TagToken):

	def parse(self, context):
		if len(self.args) > 1:
			raise Exception("@end expects either zero or one argument")

		elif isinstance(context, tag.ExtendedTagContext):

			success = False
			if len(self.args) == 1:
				try:
					endname = text.PlainStringContext(self.args[0], context).parse()
					success = (endname == context.tagtoken.name)
				except Exception:
					pass
			elif len(self.args) == 0:
				success = True

			if success:
				raise parser.LeaveContext
			else:
				if not endname:
					endname = '??'
				raise ValueError("cannot close @" + context.tagtoken.name + " with @end[[" + endname + "]]")

			
		else:
			raise Exception("unexpected @end")
