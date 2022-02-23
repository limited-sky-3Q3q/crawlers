from .proxyGetter import ProxyGetter
from src.mylogger import Logger, root


class IphaiProxy(ProxyGetter):
	name = 'ip海代理(http://www.iphai.com/)'

	HIGH_ANONYMITY_PAGE_URL = 'http://www.iphai.com/free/ng'
	HTTP_PAGE_URL = HIGH_ANONYMITY_PAGE_URL
	HTTPS_PAGE_URL = HIGH_ANONYMITY_PAGE_URL

	PAGE_START_DEFAULT = 0
	PAGE_END_DEFAULT = 1

	IP_LIST_XPATH = '//div[@class="table-responsive module"]/table/tr/td[1]/..'
	IP_XPATH = './td[1]'
	PORT_XPATH = './td[2]'
	ANONYMITY_XPATH = './td[3]'
	SCHEME_XPATH = './td[4]'
	ADDRESS_XPATH = './td[5]'

	def __init__(self, logger: Logger=root):
		super(IphaiProxy, self).__init__(logger)

	def check_anonymity(self, anonymity: str):
		return True