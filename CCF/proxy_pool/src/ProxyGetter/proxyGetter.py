import requests
from lxml import etree
import time
from lxml.etree import Element
import random

from src.mylogger import root, Logger
from src.utils import random_user_agent, check_proxy_format


# __开头函数无法重写
class ProxyGetter():
	name = ''
	# 高匿代理
	HIGH_ANONYMITY_PAGE_URL = ''
	# https代理
	HTTPS_PAGE_URL = ''
	# http代理
	HTTP_PAGE_URL = ''

	MIN_SLEEP_TIME = 1
	MAX_SLEEP_TIME = 3

	PAGE_START_DEFAULT = 0
	PAGE_END_DEFAULT = 0
	PAGE_NUM = 0

	IP_LIST_XPATH = ''
	IP_XPATH = ''
	PORT_XPATH = ''
	ANONYMITY_XPATH = ''
	SCHEME_XPATH = ''
	ADDRESS_XPATH = ''

	def __init__(self, logger: Logger=root):
		self.logger = logger
		self.session = requests.Session()
		self.session.headers = {
            'User-Agent': random_user_agent(),
		}

	def _get_element_tree(self, page_url, **kwargs):
		'''

		:param page_url:
		:param args:
		:param kwargs:
		:return:
		'''
		try:
			response = self.session.get(page_url, timeout=15, **kwargs)
		except:
			self.logger.warning('fail get page {page_url}'
			                    .format(page_url=page_url), exc_info=True)
			return None

		if response.status_code != 200:
			self.logger.warning('fail get page {page_url}, for status_code: {status_code}'
			                    .format(page_url=page_url, status_code=response.status_code))
			return None

		self.logger.debug('success get page {page_url}'
		                  .format(page_url=page_url))

		try:
			element_tree = etree.HTML(response.text)
		except:
			self.logger.warning('fail get element_tree of page {page_url}'
			                    .format(page_url=page_url), exc_info=True)
			return None

		return element_tree

	# TODO 使用代理来爬取代理
	# 只抓取高匿代理
	def get_proxies(self, page_start: int=0, page_end: int=0,
	                page_num: int=0, scheme: str='https', **kwargs):
		''' 获取[page_start, page_end)页符合scheme的proxies

		:param page_start: 起始页面index
		:param page_end: 结束页面index
		:param page_num: 总共需要抓取的页面数（为了防止西拉代理这中中间几页没有ip的情况）
		:scheme: (http, https, both) 仅获取http代理或者https代理, 或者都获取
		:kwargs
		:return:
		'''
		page_start = page_start or self.PAGE_START_DEFAULT
		page_end = page_end or self.PAGE_END_DEFAULT
		page_num = page_num or self.PAGE_NUM

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

		# 获取规定数量的页数
		if page_num > 0:
			page_index = 0
			while page_num > 0:
				page_url = PAGE_URL.format(page_index=page_index)
				proxies = self._get_proxies_from_single_page(page_url, scheme_list, **kwargs)
				if proxies is not None:
					page_num -= 1
					for proxy in proxies:
						del proxy['anonymity']
						yield proxy
				page_index += 1
				time.sleep(random.randint(self.MIN_SLEEP_TIME, self.MAX_SLEEP_TIME))
		# 获取规定范围的几页
		else:
			for page_index in range(page_start, page_end):
				print(page_index)
				# get proxies from single page
				page_url = PAGE_URL.format(page_index=page_index)
				proxies = self._get_proxies_from_single_page(page_url, scheme_list, **kwargs)
				if proxies is not None:
					for proxy in proxies:
						del proxy['anonymity']
						yield proxy

				# for proxy in self._get_proxies_from_single_page(page_url, scheme_list, **kwargs):
				# 	del proxy['anonymity']
				# 	yield proxy

				time.sleep(random.randint(self.MIN_SLEEP_TIME, self.MAX_SLEEP_TIME))

	def _parse_ip_line(self, ip_line: Element):
		''' 处理单行proxy

		:param ip_line:
		:return: dict or None
		'''
		# 获取ip、port、scheme、anonymity
		try:
			ip = ip_line.find(self.IP_XPATH).text.strip()
			port = ip_line.find(self.PORT_XPATH).text.strip()
			proxy_scheme = ip_line.find(self.SCHEME_XPATH).text.strip()
			anonymity = ip_line.find(self.ANONYMITY_XPATH).text.strip()
		except:
			self.logger.warning('fail get proxies from {name}, maybe the xpath is wrong'
			                    .format(name=self.name), exc_info=True)
			return None

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

	def _get_proxies_from_single_page(self, page_url: str, scheme_list: list, **kwargs):
		''' 处理单页

		:param page_url:
		:param scheme_list:
		:param kwargs:
		:return:
		'''
		element_tree = self._get_element_tree(page_url, **kwargs)
		if element_tree is None:
			return None

		ip_list = element_tree.xpath(self.IP_LIST_XPATH)
		if len(ip_list) <= 0:
			self.logger.warning('fail get proxies from {name}, for none proxy in {page_url}, or maybe the ip_list_xpath is wrong'
			                    .format(name=self.name, page_url=page_url))
			return None

		proxies = []
		for ip_line in ip_list:
			proxy = self._parse_ip_line(ip_line)
			if proxy is None:
				continue

			# 当前获取的proxy的scheme不在获取范围内或不是高匿代理
			if (not proxy['scheme'].lower() in scheme_list) or (not self.check_anonymity(proxy['anonymity'])):
				continue

			proxies.append(proxy)

		return proxies

	def check_anonymity(self, anonymity: str):
		''' 检测是否为高匿代理

		:param anonymity:
		:return:
		'''
		return anonymity.find('高匿') >= 0