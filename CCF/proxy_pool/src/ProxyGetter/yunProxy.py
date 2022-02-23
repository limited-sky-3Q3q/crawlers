from .proxyGetter import ProxyGetter
from src.mylogger import Logger, root


class YunProxy(ProxyGetter):
	name = '云代理(http://www.ip3366.net/)'

	HIGH_ANONYMITY_PAGE_URL = 'http://www.ip3366.net/free/?stype=1&page={page_index}'
	HTTP_PAGE_URL = HIGH_ANONYMITY_PAGE_URL
	HTTPS_PAGE_URL = HIGH_ANONYMITY_PAGE_URL

	PAGE_START_DEFAULT = 1
	PAGE_END_DEFAULT = 4

	IP_LIST_XPATH = '//div[@id="list"]/table/tbody/tr'
	IP_XPATH = './td[1]'
	PORT_XPATH = './td[2]'
	ANONYMITY_XPATH = './td[3]'
	SCHEME_XPATH = './td[4]'
	ADDRESS_XPATH = './td[5]'

	def __init__(self, logger: Logger=root):
		super(YunProxy, self).__init__(logger)

	def check_anonymity(self, anonymity: str):
		return True