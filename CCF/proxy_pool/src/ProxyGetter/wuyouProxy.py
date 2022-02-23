from lxml.etree import Element
import time

from .proxyGetter import ProxyGetter
from src.mylogger import root, Logger
from src.utils import check_proxy_format


class WuyouProxy(ProxyGetter):
	name = '无忧代理(http://www.data5u.com/)'

	HIGH_ANONYMITY_PAGE_URL = 'http://www.data5u.com'
	HTTPS_PAGE_URL = HIGH_ANONYMITY_PAGE_URL
	HTTP_PAGE_URL = HIGH_ANONYMITY_PAGE_URL

	PAGE_START_DEFAULT = 0
	PAGE_END_DEFAULT = 1

	IP_LIST_XPATH = '//div[@class="wlist"]/ul/li[2]/ul[position() > 1]'
	IP_XPATH = './span[1]/li'
	PORT_XPATH = './span[2]/li'
	ANONYMITY_XPATH = './span[3]/li'
	SCHEME_XPATH = './span[4]/li'
	ADDRESS_XPATH = './span[6]/li'

	def __init__(self, logger: Logger=root):
		super(WuyouProxy, self).__init__(logger)

	def _parse_ip_line(self, ip_line: Element):
		''' 处理单行proxy

		:param ip_line:
		:return: dict or None
		'''
		# 获取ip、port、scheme、anonymity
		try:
			ip = ip_line.find(self.IP_XPATH).text.strip()
			port = ip_line.find(self.PORT_XPATH).get('class').replace('port', '').strip()
			proxy_scheme = ip_line.find(self.SCHEME_XPATH).text.strip()
			anonymity = ip_line.find(self.ANONYMITY_XPATH).text.strip()
		except:
			self.logger.warning('fail get proxies from {name}, maybe the xpath is wrong'
			                    .format(name=self.name), exc_info=True)
			return None

		# js加密port
		port = port.replace('A', '0')\
			.replace('B', '1')\
			.replace('C', '2')\
			.replace('D', '3')\
			.replace('E', '4')\
			.replace('F', '5')\
			.replace('G', '6')\
			.replace('H', '7')\
			.replace('I', '8')\
			.replace('Z', '9')
		port = str(int(int(port) / 8))

		# 检测proxy的format
		proxy = ip + ':' + port
		if not check_proxy_format(proxy):
			self.logger.warning('wrong format proxy <{proxy}>'
			                    .format(proxy=proxy))
			return None

		# 获取proxy的所在地
		try:
			address = ip_line.find(self.ADDRESS_XPATH).text.strip()
		except:
			self.logger.debug('fail get proxy\'s address from {name}, maybe the address_xpath is wrong'
			                  .format(name=self.name), exc_info=True)
			address = ''

		return {
			'proxy': proxy,
			'scheme': proxy_scheme,
			'anonymity': anonymity,
			'address': address,
			'access_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
			'source': self.name
		}
