from .proxyGetter import ProxyGetter
from src.mylogger import Logger, root


class QiyunProxy(ProxyGetter):
	name = '齐云代理(https://www.7yip.cn/free/)'

	HIGH_ANONYMITY_PAGE_URL = 'https://www.7yip.cn/free/?action=china&page={page_index}'
	HTTP_PAGE_URL = HIGH_ANONYMITY_PAGE_URL
	HTTPS_PAGE_URL = HIGH_ANONYMITY_PAGE_URL

	PAGE_START_DEFAULT = 1
	PAGE_END_DEFAULT = 5

	IP_LIST_XPATH = '//div[@class="container"]/table/tbody/tr'
	IP_XPATH = './td[1][@data-title="IP"]'
	PORT_XPATH = './td[2][@data-title="PORT"]'
	ANONYMITY_XPATH = './td[3][@data-title="匿名度"]'
	SCHEME_XPATH = './td[4][@data-title="类型"]'
	ADDRESS_XPATH = './td[5][@data-title="位置"]'

	def __init__(self, logger: Logger=root):
		super(QiyunProxy, self).__init__(logger)