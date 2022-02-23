import random

from lxml import etree
from lxml.etree import Element
import time

from .proxyGetter import ProxyGetter
from src.mylogger import Logger, root
from src.utils import check_proxy_format


class XilaProxy(ProxyGetter):
	name = '西拉代理(http://www.xiladaili.com/)'

	HIGH_ANONYMITY_PAGE_URL = 'http://www.xiladaili.com/gaoni/{page_index}'
	HTTP_PAGE_URL = 'http://www.xiladaili.com/http/{page_index}'
	# HTTPS_PAGE_URL = 'http://www.xiladaili.com/https/{page_index}'
	HTTPS_PAGE_URL = 'http://www.xiladaili.com/gaoni/{page_index}'

	PAGE_START_DEFAULT = 1
	PAGE_END_DEFAULT = 20
	PAGE_NUM = 0

	IP_LIST_XPATH = '//table[@class="fl-table"]/tbody/tr'
	IP_XPATH = './td[1]'
	ANONYMITY_XPATH = './td[3]'
	SCHEME_XPATH = './td[2]'
	ADDRESS_XPATH = './td[4]'

	MIN_SLEEP_TIME = 3
	MAX_SLEEP_TIME = 5

	def __init__(self, logger: Logger=root):
		super(XilaProxy, self).__init__(logger)

	def _parse_ip_line(self, ip_line: Element):
		''' 处理单行proxy

		:param ip_line:
		:return: dict or None
		'''
		# 获取ip、port、scheme、anonymity
		try:
			ip = ip_line.find(self.IP_XPATH).text.strip()
			proxy_scheme = ip_line.find(self.SCHEME_XPATH).text.strip()
			anonymity = ip_line.find(self.ANONYMITY_XPATH).text.strip()
		except:
			self.logger.warning('fail get proxies from {name}, maybe the xpath is wrong'
			                    .format(name=self.name), exc_info=True)
			return None

		# 检测proxy的format
		proxy = ip
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

		if proxy_scheme == 'HTTP代理':
			proxy_scheme = 'HTTP'
		elif proxy_scheme == 'HTTPS代理':
			proxy_scheme = 'HTTPS'
		elif proxy_scheme == 'HTTP,HTTPS代理':
			proxy_scheme = 'HTTP/HTTPS'

		return {
			'proxy': proxy,
			'scheme': proxy_scheme,
			'anonymity': anonymity,
			'address': address,
			'access_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
			'source': self.name
		}

	# FIXME 暂时改动
	def get_proxies(self, page_start: int=0, page_end: int=0,
	                page_num: int=0, scheme: str='https', **kwargs):
		if scheme == 'http':
			scheme_list = ['http', 'http/https', 'https/http']
			PAGE_URL = self.HTTP_PAGE_URL
		elif scheme == 'https':
			scheme_list = ['https', 'http/https', 'https/http']
			PAGE_URL = self.HTTPS_PAGE_URL
		elif scheme == 'both':
			scheme_list = ['http', 'https', 'http/https', 'https/http']
			PAGE_URL = self.HIGH_ANONYMITY_PAGE_URL
		else:
			self.logger.warning('fail get proxies from {name}, for error scheme input'
			                    .format(name=self.name))
			return None

		MAX_PROXY_NUM = 1000
		MAX_PAGE_INDEX = 30

		page_index = 1
		proxy_num = 0
		while page_index <= MAX_PAGE_INDEX:
			print(page_index)
			page_url = PAGE_URL.format(page_index=page_index)
			proxies = self._get_proxies_from_single_page(page_url, scheme_list, **kwargs)
			if proxies is not None:
				for proxy in proxies:
					del proxy['anonymity']
					yield proxy
					proxy_num += 1

			if proxy_num >= MAX_PROXY_NUM:
				break
			time.sleep(random.randint(self.MIN_SLEEP_TIME, self.MAX_SLEEP_TIME))
			page_index += 1