import tag
import parser

def token_class():
	return EndTagToken

class EndTagToken(tag.TagToken):

	def parse(self, context):
		if len(self.args) > 0:
			raise Exception("@end tag expects no argument")
		elif isinstance(context, tag.ExtendedTagContext):
			raise parser.LeaveContext
		else:
			raise Exception("unexpected @end")
