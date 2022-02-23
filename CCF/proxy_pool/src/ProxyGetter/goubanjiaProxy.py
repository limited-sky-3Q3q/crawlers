from lxml.etree import Element
import time

from .proxyGetter import ProxyGetter
from src.mylogger import Logger, root
from src.utils import check_proxy_format


class GoubanjiaProxy(ProxyGetter):

	name = '全网代理(http://www.goubanjia.com/)'

	HIGH_ANONYMITY_PAGE_URL = 'http://www.goubanjia.com/'
	HTTP_PAGE_URL = HIGH_ANONYMITY_PAGE_URL
	HTTPS_PAGE_URL = HIGH_ANONYMITY_PAGE_URL

	PAGE_START_DEFAULT = 1
	PAGE_END_DEFAULT = 2

	IP_LIST_XPATH = '//div[@class="container-fluid"]//table/tbody/tr'
	IP_XPATH = './td[1][@class="ip"]/*[not (contains(@class, "port"))][not (contains(@style, "none"))]//text()'
	PORT_XPATH = './td[1]/*[contains(@class, "port")]'
	ANONYMITY_XPATH = './td[2]/a'
	SCHEME_XPATH = './td[3]/a'
	ADDRESS_XPATH = './td[4]/a'

	def __init__(self, logger: Logger=root):
		super(GoubanjiaProxy, self).__init__(logger)

	def _parse_ip_line(self, ip_line: Element):
		''' 处理单行proxy

		:param ip_line:
		:return: dict or None
		'''
		# 获取ip、port、scheme、anonymity
		try:
			ip = ''.join(ip_line.xpath(self.IP_XPATH)).strip()
			port = ip_line.xpath(self.PORT_XPATH)[0].get('class').replace('port', '').strip()
			proxy_scheme = ip_line.find(self.SCHEME_XPATH).text.strip()
			anonymity = ip_line.find(self.ANONYMITY_XPATH).text.strip()
		except:
			self.logger.warning('fail get proxies from {name}, maybe the xpath is wrong'
			                    .format(name=self.name), exc_info=True)
			return None

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
