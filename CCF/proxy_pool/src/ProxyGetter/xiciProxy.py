from .proxyGetter import ProxyGetter
from src.mylogger import Logger, root


class XICIProxy(ProxyGetter):
	name = '西刺代理(https://www.xicidaili.com)'
	# 高匿代理
	HIGH_ANONYMITY_PAGE_URL = 'https://www.xicidaili.com/nn/{page_index}'
	# https代理
	HTTPS_PAGE_URL = 'https://www.xicidaili.com/wn/{page_index}'
	# http代理
	HTTP_PAGE_URL = 'https://www.xicidaili.com/wt/{page_index}'

	PAGE_START_DEFAULT = 1
	PAGE_END_DEFAULT = 10

	IP_LIST_XPATH = '//table[@id="ip_list"]/tr/td[2]/..'
	IP_XPATH = './td[2]'
	PORT_XPATH = './td[3]'
	ANONYMITY_XPATH = './td[5]'
	SCHEME_XPATH = './td[6]'
	ADDRESS_XPATH = './td[4]/a'

	MAX_SLEEP_TIME = 5
	MIN_SLEEP_TIME = 3

	def __init__(self, logger: Logger=root):
		super(XICIProxy, self).__init__(logger)