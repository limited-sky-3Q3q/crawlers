from .proxyGetter import ProxyGetter
from src.mylogger import Logger, root


class FreeipProxy(ProxyGetter):
	name = '免费代理(https://www.freeip.top/)'

	HIGH_ANONYMITY_PAGE_URL = 'https://www.freeip.top/?page={page_index}&anonymity=2'
	HTTP_PAGE_URL = 'https://www.freeip.top/?page={page_index}&protocol=http&anonymity=2'
	HTTPS_PAGE_URL = 'https://www.freeip.top/?page={page_index}&protocol=https&anonymity=2'

	PAGE_START_DEFAULT = 1
	PAGE_END_DEFAULT = 4

	IP_LIST_XPATH = '//table[@class="layui-table"]/tbody/tr'
	IP_XPATH = './td[1]'
	PORT_XPATH = './td[2]'
	ANONYMITY_XPATH = './td[3]'
	SCHEME_XPATH = './td[4]'
	ADDRESS_XPATH = './td[5]'

	def __init__(self, logger: Logger=root):
		super(FreeipProxy, self).__init__(logger)