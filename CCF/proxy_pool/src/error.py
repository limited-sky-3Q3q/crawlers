class UnknowImgTypeError(Exception):
	def __init__(self):
		super().__init__()

	def __str__(self):
		return repr('unknow img type')


class UnknowWebsiteError(Exception):
	def __init__(self):
		super().__init__()

	def __str__(self):
		return repr('the website is not exist in CHECK_WEBSITES')