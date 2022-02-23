from lxml.etree import Element
import os
import shutil
import time

from .proxyGetter import ProxyGetter
from src.mylogger import Logger, root
from src.utils import url_join, image_to_string, get_img_type, check_proxy_format


class MipuProxy(ProxyGetter):
	name = '米扑代理(https://proxy.mimvp.com/)'

	HIGH_ANONYMITY_PAGE_URL = 'https://proxy.mimvp.com/freesole?proxy=in_hp&sort=&page={page_index}'
	HTTP_PAGE_URL = HIGH_ANONYMITY_PAGE_URL
	HTTPS_PAGE_URL = HIGH_ANONYMITY_PAGE_URL

	# 免费只能查看第一页
	PAGE_START_DEFAULT = 1
	PAGE_END_DEFAULT = 2

	IP_LIST_XPATH = '//table[@class="mimvp-tbl free-proxylist-tbl"]/tbody/tr'
	IP_XPATH = './td[2][@class="free-proxylist-tbl-proxy-ip"]'
	# port为图片，需要图片识别
	PORT_XPATH = './td[3][@class="free-proxylist-tbl-proxy-port"]/img'
	ANONYMITY_XPATH = './td[5][@class="free-proxylist-tbl-proxy-anonymous"]'
	SCHEME_XPATH = './td[4][@class="free-proxylist-tbl-proxy-type"]'
	ADDRESS_XPATH = './td[6][@class="free-proxylist-tbl-proxy-country"]'

	def __init__(self, logger: Logger=root):
		super(MipuProxy, self).__init__(logger)

	def __get_port_from_img(self, img_url: str):
		# 创建临时目录
		TEMP_FOLDER = './temp'
		if not os.path.exists(TEMP_FOLDER):
			os.makedirs(TEMP_FOLDER)

		# 下载图片
		try:
			response = self.session.get(img_url)
		except:
			shutil.rmtree(TEMP_FOLDER)
			self.logger.warning('fail get port, for fail download img of {img_url}'
			                    .format(img_url=img_url))
			return None

		img_content = response.content

		# get img type
		try:
			img_type = get_img_type(img_content[0:4])
		except:
			shutil.rmtree(TEMP_FOLDER)
			self.logger.warning('fail get port', exc_info=True)
			return None

		# 写入临时图片
		TEMP_IMG = './temp/temp.{img_type}'.format(img_type=img_type)
		with open(TEMP_IMG, 'wb') as f:
			f.write(img_content)

		# 图片识别文字
		try:
			port = image_to_string(TEMP_IMG)
			shutil.rmtree(TEMP_FOLDER)
			return port
		except:
			shutil.rmtree(TEMP_FOLDER)
			self.logger.warning('fail get port', exc_info=True)
			return None

	def _parse_ip_line(self, ip_line: Element):
		try:
			ip = ip_line.find(self.IP_XPATH).text.strip()
			port_img_url = url_join('https://proxy.mimvp.com/', ip_line.find(self.PORT_XPATH).get('src').strip())
			proxy_scheme = ip_line.find(self.SCHEME_XPATH).text.strip()
			anonymity = ip_line.find(self.ANONYMITY_XPATH).text.strip()
		except:
			self.logger.warning('fail get proxies from {name}, maybe the xpath is wrong'
			                    .format(name=self.name), exc_info=True)
			return None

		port = self.__get_port_from_img(port_img_url) or ''

		# 检测proxy的format
		proxy = ip + ':' + port
		if not check_proxy_format(proxy):
			self.logger.warning('wrong format proxy <{proxy}>'
			                    .format(proxy=proxy))
			return None

		# 获取proxy的所在地
		try:
			address = ''.join([text.strip() for text in ip_line.find(self.ADDRESS_XPATH).xpath('.//text()')])
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