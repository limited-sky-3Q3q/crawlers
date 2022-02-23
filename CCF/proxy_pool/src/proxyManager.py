import time
from threading import Thread
import random

from .ProxyGetter import proxy_getter_list
from .settings import PROXY_GETTER_SETTINGS, BASE_CHECK_WEBSITE, PROXY_MIN_SLEEP_TIME, PROXY_MAX_SLEEP_TIME, PROXY_SCHEME, CHECK_WEBSITES
from .mylogger import root, Logger
from .proxy import Proxy, RawProxy, UsefulProxy
from .proxyDB import ProxyDB
from .utils import singleton
from .ProxyGetter import XilaProxy


# useful proxies允许连续检测失败最大次数
MAX_FAIL_COUNTS = 1


@singleton
class ProxyManager():
	CHECK_RAW_PROXIES_THREAD_COUNTS = 20
	CHECK_USEFUL_PROXIES_THREAD_COUNTS = 20

	# FIXME xila代理开始的页面
	PAGE_START = 1

	def __init__(self, proxy_db: ProxyDB=None, logger: Logger=root):
		self.proxy_db = proxy_db or ProxyDB()
		self.logger = logger

	def get_free_proxies(self):
		''' 获取免费代理并入库

		:return:
		'''
		proxies = []
		for proxy_getter in proxy_getter_list:
			proxy_getter_name = proxy_getter.__name__
			proxy_getter_setting = PROXY_GETTER_SETTINGS.get(proxy_getter_name)

			# 该proxy_getter禁用(默认禁用)
			if not proxy_getter_setting.get('enable', False):
				continue

			args = proxy_getter_setting.get('args', {'scheme': PROXY_SCHEME})
			proxies_dicts = proxy_getter(self.logger).get_proxies(**args)
			# 该列表为去掉重复raw_proxy
			for proxy_dict in proxies_dicts:
				if proxy_dict['proxy'] not in proxies:
					self.save_raw_proxy(proxy_dict)
					proxies.append(proxy_dict['proxy'])
				else:
					self.logger.debug('raw proxy {proxy} exists'.format(proxy=proxy_dict['proxy']))

	# FIXME 暂时只大量抓取xila代理
	# def get_free_proxies(self):
	# 	proxies = []
	# 	proxies_dicts = XilaProxy(self.logger).get_proxies()
	#
	# 	# 该列表为去掉重复raw_proxy
	# 	for proxy_dict in proxies_dicts:
	# 		if proxy_dict['proxy'] not in proxies:
	# 			self.save_raw_proxy(proxy_dict)
	# 			proxies.append(proxy_dict['proxy'])
	# 		else:
	# 			self.logger.debug('raw proxy {proxy} exists'.format(proxy=proxy_dict['proxy']))

	def check_raw_proxies(self):
		''' 多线程检测raw proxies

		:return:
		'''
		def __get_and_check_raw_proxy():
			while True:
				try:
					raw_proxy = self.proxy_db.blpop_raw_proxy()[1]
				except:
					self.logger.warning('fail blpop_raw_proxy', exc_info=True)
					continue

				# 为防止未知bug导致线程退出
				try:
					self.check_raw_proxy(raw_proxy, BASE_CHECK_WEBSITE)
				except:
					self.logger.warning('something error', exc_info=True)

		th_list = []
		for _ in range(0, self.CHECK_RAW_PROXIES_THREAD_COUNTS):
			th = Thread(target=__get_and_check_raw_proxy, name='check_raw_proxies_thread_{index}'
			            .format(index=_))
			self.logger.debug('check_raw_proxies_thread_{index} start'
			                  .format(index=_))
			th.start()
			th_list.append(th)

		for th in th_list:
			th.join()

	# def check_useful_proxies(self):
	# 	''' 多线程检测useful proxies
	#
	# 	:return:
	# 	'''
	# 	def __check_single_useful_proxies():
	# 		while True:
	# 			try:
	# 				useful_proxy = self.proxy_db.blpop_check_useful_proxy()[1]
	# 			except:
	# 				self.logger.warning('fail blpop_useful_proxy', exc_info=True)
	# 				continue
	#
	# 			self.check_useful_proxy(useful_proxy, BASE_CHECK_WEBSITE)
	#
	# 	th_lsit = []
	# 	for _ in range(0, self.CHECK_USEFUL_PROXIES_THREAD_COUNTS):
	# 		th = Thread(target=__check_single_useful_proxies, name='check_useful_proxies_thread_{index}'
	# 		            .format(index=_))
	# 		self.logger.debug('check_useful_proxies_thread_{index} start'
	# 		                  .format(index=_))
	# 		th.start()
	# 		th_lsit.append(th)
	#
	# 	for th in th_lsit:
	# 		th.join()

	def check_useful_proxies(self, website: str):
		''' 多线程检测{website}_useful_proxies

		:param website:
		:return:
		'''
		def __check_single_useful_proxies(website):
			while True:
				try:
					useful_proxy = self.proxy_db.blpop_check_useful_proxy(website)[1]
				except:
					self.logger.warning('fail blpop_{website}_useful_proxy', exc_info=True)
					continue

				# 为防止未知bug导致线程退出
				try:
					self.check_useful_proxy(useful_proxy, website)
				except:
					self.logger.warning('something error', exc_info=True)

		th_lsit = []
		for _ in range(0, self.CHECK_USEFUL_PROXIES_THREAD_COUNTS):
			th = Thread(target=__check_single_useful_proxies, args=(website,),
			            name='{website}_check_useful_proxies_thread_{index}'.format(index=_, website=website))
			self.logger.debug('{website}_check_useful_proxies_thread_{index} start'
			                  .format(index=_, website=website))
			th.start()
			th_lsit.append(th)

		for th in th_lsit:
			th.join()

	# def save_proxy(self, proxy_dict: dict, useful_proxy: bool=False):
	# 	''' 存储一个proxy
	#
	# 	:param proxy_dict:
	# 	:param useful_proxy: 是存入useful_proxies列表还是存入raw_proxies列表
	# 	:return:
	# 	'''
	# 	proxy = proxy_dict['proxy']
	# 	proxy_dict.update({'proxy': ''})
	# 	try:
	# 		if useful_proxy:
	# 			self.proxy_db.rpush_useful_proxy(proxy)
	# 		else:
	# 			self.proxy_db.rpush_raw_proxy(proxy)
	#
	# 		self.proxy_db.hmset_proxy(proxy, proxy_dict)
	# 		self.logger.debug('success save proxy {proxy}'
	# 		                  .format(proxy=proxy))
	# 		return True
	# 	except:
	# 		self.logger.warning('fail save proxy {proxy}'
	# 		                    .format(proxy=proxy), exc_info=True)
	# 		return False

	def save_useful_proxy(self, raw_proxy_dict: dict, website: str):
		''' 存储一个{website}_useful_proxy

		:param raw_proxy_dict:
		:param website:
		:return:
		'''
		proxy = raw_proxy_dict['proxy']
		try:
			# 判断是否已经存在
			if self.proxy_db.exists_proxy(proxy, website):
				self.logger.debug('{website}_{proxy} has already exists'
				                  .format(website=website, proxy=proxy))
				return False

			self.proxy_db.rpush_useful_proxy(website, proxy)

			useful_proxy_obj = UsefulProxy(raw_proxy_dict, website=website)
			self.proxy_db.hmset_proxy(proxy, useful_proxy_obj.to_dict(), website)
			self.logger.debug('success save proxy {website}_{proxy}'
			                  .format(proxy=proxy, website=website))
			return True
		except:
			self.logger.warning('fail save proxy {website}_{proxy}'
			                    .format(proxy=proxy, website=website), exc_info=True)
			return False

	def save_raw_proxy(self, raw_proxy_dict: dict):
		''' 存储一个raw_proxy

		:param raw_proxy_dict:
		:return:
		'''
		proxy = raw_proxy_dict['proxy']
		try:
			self.proxy_db.rpush_raw_proxy(proxy)
			self.proxy_db.hmset_proxy(proxy, raw_proxy_dict)
			self.logger.debug('success save raw proxy {proxy}'
			                  .format(proxy=proxy))
			return True
		except:
			self.logger.warning('fail save raw proxy {proxy}'
			                    .format(proxy=proxy), exc_info=True)
			return False

	# def update_proxy(self, proxy: Proxy):
	# 	''' 更新一个proxy的信息
	#
	# 	:param proxy:
	# 	:return:
	# 	'''
	# 	try:
	# 		proxy_dict = proxy.to_dict()
	# 		proxy_dict['proxy'] = ''
	#
	# 		self.proxy_db.hmset_proxy(proxy.proxy, proxy_dict)
	# 		self.logger.debug('success update proxy {proxy}'
	# 		                  .format(proxy=proxy.proxy))
	# 		return True
	# 	except:
	# 		self.logger.warning('fail update proxy {proxy}'
	# 		                    .format(proxy=proxy.proxy), exc_info=True)
	# 		return False

	def update_useful_proxy(self, proxy_dict, website: str):
		''' 更新一个proxy的信息

		:param proxy:
		:param website:
		:return:
		'''
		try:
			self.proxy_db.hmset_proxy(proxy_dict['proxy'], proxy_dict, website)
			self.logger.debug('success update {website}_useful_proxy {proxy}'
			                  .format(proxy=proxy_dict['proxy'], website=website))
			return True
		except:
			self.logger.warning('fail update {website}_useful_proxy {proxy}'
			                    .format(proxy=proxy_dict['proxy'], website=website), exc_info=True)
			return False

	# def check_raw_proxy(self, raw_proxy: str, website_url: str):
	# 	''' 检测一个raw_proxy的可用性
	#
	# 	:param raw_proxy:
	# 	:param website_url:
	# 	:return:
	# 	'''
	# 	self.logger.debug('checking raw_proxy {proxy}'
	# 	                  .format(proxy=raw_proxy))
	#
	# 	result = Proxy.check_usability(raw_proxy, website_url)
	#
	# 	if result:
	# 		self.logger.info('success check raw-proxy {proxy} {website_url}'
	# 		                 .format(proxy=raw_proxy, website_url=website_url))
	# 		try:
	# 			raw_proxy_dict = self.proxy_db.hgetall_proxy(raw_proxy)
	# 		except:
	# 			self.logger.warning('fail update new useful_proxy {proxy} info, for fail hgetall proxy'
	# 			                    .format(proxy=raw_proxy), exc_info=True)
	# 			return False
	#
	# 		# 更新raw_proxy的信息
	# 		raw_proxy_dict['proxy'] = raw_proxy
	# 		raw_proxy_obj = Proxy.from_dict(raw_proxy_dict)
	#
	# 		raw_proxy_obj.state = 1
	# 		raw_proxy_obj.check_counts = 1
	# 		raw_proxy_obj.last_check_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	# 		# 更新proxy的信息，并存入useful_proxies列表中
	# 		self.save_proxy(raw_proxy_obj.to_dict(), useful_proxy=True)
	# 		return True
	# 	else:
	# 		self.logger.info('fail check raw-proxy {proxy} {website_url}'
	# 		                 .format(proxy=raw_proxy, website_url=website_url))
	# 		self.del_proxy(raw_proxy)
	# 		return False

	def check_raw_proxy(self, raw_proxy: str, website_url: str):
		''' 检测一个raw_proxy的可用性以及是否是高匿

		:param raw_proxy:
		:param website_url:
		:return:
		'''
		self.logger.debug('checking raw_proxy {proxy}'
		                  .format(proxy=raw_proxy))

		result = Proxy.check_usability(raw_proxy, website_url)

		if result:
			# 检测到代理可用后再检测是否是高匿代理
			check_anonymity_result = Proxy.check_high_anonymity(raw_proxy)
			if check_anonymity_result:
				self.logger.info('success check raw-proxy {proxy} {website_url}'
				                 .format(proxy=raw_proxy, website_url=website_url))
				try:
					raw_proxy_dict = self.proxy_db.hgetall_proxy(raw_proxy)
				except:
					self.logger.warning('fail update new useful_proxy {proxy} info, for fail hgetall proxy'
					                    .format(proxy=raw_proxy), exc_info=True)
					return False
				finally:
					self.del_raw_proxy(raw_proxy)

				# 存入{website}_proxy
				for website in CHECK_WEBSITES.keys():
					self.save_useful_proxy(raw_proxy_dict, website)
				return True
			# 不是高匿代理
			else:
				self.logger.warning('fail check raw-proxy {proxy}, for not high anonymity'
				                    .format(proxy=raw_proxy))
		# 代理不可用
		else:
			self.logger.info('fail check raw-proxy {proxy} {website_url}'
			                 .format(proxy=raw_proxy, website_url=website_url))

		self.del_raw_proxy(raw_proxy)
		return False

	# def check_useful_proxy(self, useful_proxy: str, website_url: str):
	# 	''' 检测一个在useful_proxies列表内的proxy的可用性
	#
	# 	:param useful_proxy:
	# 	:param website_url:
	# 	:return:
	# 	'''
	# 	self.logger.debug('checking useful_proxy {proxy}'
	# 	                  .format(proxy=useful_proxy))
	#
	# 	try:
	# 		useful_proxy_dict = self.proxy_db.hgetall_proxy(useful_proxy)
	# 	except:
	# 		self.logger.warning('fail check useful_proxy {proxy} {website_url], for fail hgetall proxy'
	# 		                    .format(proxy=useful_proxy, website_url=website_url), exc_info=True)
	# 		return False
	#
	# 	useful_proxy_dict['proxy'] = useful_proxy
	# 	useful_proxy_obj = Proxy.from_dict(useful_proxy_dict)
	#
	# 	result = Proxy.check_usability(useful_proxy, website_url)
	#
	# 	if result:
	# 		self.logger.info('success check useful-proxy {proxy} {website_url}'
	# 		                 .format(proxy=useful_proxy, website_url=website_url))
	# 		useful_proxy_obj.state = 1
	# 		# 检测成功后，fail_counts清零，需要连续MAX_FAIL_COUNTS次失败后才删除该proxy
	# 		useful_proxy_obj.fail_counts = 0
	# 	else:
	# 		self.logger.info('fail check useful-proxy {proxy} {website_url}'
	# 		                 .format(proxy=useful_proxy, website_url=website_url))
	# 		useful_proxy_obj.state = 0
	# 		useful_proxy_obj.fail_counts += 1
	# 		if useful_proxy_obj.fail_counts >= MAX_FAIL_COUNTS:
	# 			self.del_useful_proxy(useful_proxy)
	# 			return False
	#
	# 	useful_proxy_obj.check_counts += 1
	# 	useful_proxy_obj.last_check_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	# 	# 更新proxy信息
	# 	self.update_proxy(useful_proxy_obj)
	# 	return result

	def check_useful_proxy(self, useful_proxy: str, website: str):
		''' 检测一个在{website}_useful_proxies列表内的proxy的可用性

		:param useful_proxy:
		:param website:
		:return:
		'''
		self.logger.debug('checking {website}_useful_proxy {proxy}'
		                  .format(proxy=useful_proxy, website=website))

		try:
			useful_proxy_dict = self.proxy_db.hgetall_proxy(useful_proxy, website)
			if useful_proxy_dict == {}:
				self.logger.debug('{website}_useful_proxy {useful_proxy} was been already remove'
				                  .format(website=website, useful_proxy=useful_proxy))
				return False
		except:
			self.logger.warning('fail check useful_proxy {proxy} {website_url], for fail hgetall proxy'
			                    .format(proxy=useful_proxy, website_url=CHECK_WEBSITES[website]['url']), exc_info=True)
			return False

		website_url = CHECK_WEBSITES[website]['url']
		result = Proxy.check_usability(useful_proxy, website_url)

		if result:
			self.logger.info('success check useful-proxy {proxy} {website_url}'
			                 .format(proxy=useful_proxy, website_url=website_url))
			useful_proxy_dict['state'] = 1
			# 检测成功后，fail_counts清零，需要连续MAX_FAIL_COUNTS次失败后才删除该proxy
			useful_proxy_dict['fail_counts'] = 0
		else:
			self.logger.info('fail check useful-proxy {proxy} {website_url}'
			                 .format(proxy=useful_proxy, website_url=website_url))
			useful_proxy_dict['state'] = 0
			useful_proxy_dict['fail_counts'] = int(useful_proxy_dict['fail_counts']) + 1
			if int(useful_proxy_dict['fail_counts']) >= MAX_FAIL_COUNTS:
				self.del_useful_proxy(useful_proxy, website)
				return False

		useful_proxy_dict['check_counts'] = int(useful_proxy_dict['check_counts']) + 1
		useful_proxy_dict['last_check_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
		# 更新proxy信息
		self.update_useful_proxy(useful_proxy_dict, website)
		return result

	# def del_proxy(self, proxy_key: str, useful_proxy: bool=False):
	# 	''' 删除掉一个代理
	#
	# 	:param proxy:
	# 	:param useful_proxy:
	# 	:return:
	# 	'''
	# 	try:
	# 		if useful_proxy:
	# 			result = self.proxy_db.del_useful_proxy(proxy_key)
	# 		else:
	# 			result = self.proxy_db.del_proxy(proxy_key)
	#
	# 		if result:
	# 			self.logger.debug('success delete proxy {proxy}'
	# 			                 .format(proxy=proxy_key))
	# 			return True
	# 		else:
	# 			self.logger.warning('fail delete proxy {proxy}'
	# 			                    .format(proxy=proxy_key))
	# 			return False
	# 	except:
	# 		self.logger.warning('fail delete proxy {proxy}'
	# 		                    .format(proxy=proxy_key), exc_info=True)
	# 		return False

	def del_raw_proxy(self, raw_proxy_key: str):
		''' 删除掉一个raw proxy

		:param raw_proxy_key:
		:return:
		'''
		try:
			result = self.proxy_db.del_proxy(raw_proxy_key)

			if result:
				self.logger.debug('success delete raw proxy {proxy}'
				                 .format(proxy=raw_proxy_key))
				return True
			else:
				self.logger.warning('fail delete raw proxy {proxy}'
				                    .format(proxy=raw_proxy_key))
				return False
		except:
			self.logger.warning('fail delete raw proxy {proxy}'
			                    .format(proxy=raw_proxy_key), exc_info=True)
			return False

	# def del_useful_proxy(self, proxy_key: str):
	# 	''' 删除掉一个曾今可用但现在不可用的代理
	#
	# 	:param proxy:
	# 	:return:
	# 	'''
	# 	result = self.del_proxy(proxy_key, useful_proxy=True)
	# 	if result:
	# 		self.logger.info('success remove useful_proxy {proxy}'
	# 		                 .format(proxy=proxy_key))
	# 		return True
	# 	else:
	# 		return False

	def del_useful_proxy(self, proxy_key: str, website: str):
		''' 删除掉一个曾今可用但现在不可用的代理

		:param proxy:
		:param website:
		:return:
		'''
		try:
			result = self.proxy_db.del_useful_proxy(proxy_key, website)
			if result:
				self.logger.info('success remove {website}_useful_proxy {proxy}'
				                 .format(proxy=proxy_key, website=website))
				return True
			else:
				return False
		except:
			self.logger.warning('fail remove {website}_useful_proxy {proxy}'
			                    .format(website=website, proxy=proxy_key), exc_info=True)
			return False

	# def get_all_useful_proxies(self):
	# 	''' 获取所有useful proxy
	#
	# 	:return:
	# 	'''
	# 	try:
	# 		useful_proxies_num = self.proxy_db.llen_useful_proxies()
	# 		useful_proxies_list = self.proxy_db.lrange_useful_proxies(0, useful_proxies_num)
	# 		self.logger.debug('success get all useful-proxies')
	# 		return useful_proxies_list
	# 	except:
	# 		self.logger.warning('fail lrange useful-proxies', exc_info=True)
	# 		return []

	def get_all_useful_proxies(self, website: str):
		''' 获取所有{website}_useful_proxies

		:param website:
		:return:
		'''
		try:
			useful_proxies_num = self.proxy_db.llen_useful_proxies(website)
			useful_proxies_list = self.proxy_db.lrange_useful_proxies(website, 0, useful_proxies_num)
			self.logger.debug('success get all {website}_useful-proxies'
			                  .format(website=website))
			return useful_proxies_list
		except:
			self.logger.warning('fail lrange {website}_useful-proxies'
			                    .format(website=website), exc_info=True)
			return []

	# def rpush_check_useful_proxies(self):
	# 	''' 将useful proxies推入check_useful_proxies列表中检测
	#
	# 	:return:
	# 	'''
	# 	useful_proxies_list = self.get_all_useful_proxies()
	# 	if len(useful_proxies_list) <= 0:
	# 		self.logger.debug('useful proxies list empty')
	# 		return False
	#
	# 	try:
	# 		self.proxy_db.rpush_check_useful_proxy(*useful_proxies_list)
	# 		return True
	# 	except:
	# 		self.logger.warning('fail rpush check_useful_proxies', exc_info=True)
	# 		return False

	def rpush_check_useful_proxies(self, website: str):
		''' 将{website}_useful_proxies推入{website}_check_useful_proxies列表中检测

		:param website:
		:return:
		'''
		useful_proxies_list = self.get_all_useful_proxies(website)
		if len(useful_proxies_list) <= 0:
			self.logger.debug('useful proxies list empty')
			return False

		try:
			self.proxy_db.rpush_check_useful_proxy(website, *useful_proxies_list)
			return True
		except:
			self.logger.warning('fail rpush {website}_check_useful_proxies'
			                    .format(website=website), exc_info=True)
			return False

	# def get_useful_proxies_num(self):
	# 	''' 获取useful-proxies的数量
	#
	# 	:return:
	# 	'''
	# 	try:
	# 		useful_proxies_num = self.proxy_db.llen_useful_proxies()
	# 		return useful_proxies_num
	# 	except:
	# 		self.logger.warning('fail llen useful-proxies', exc_info=True)
	# 		return None

	def get_useful_proxies_num(self, website: str):
		''' 获取useful-proxies的数量

		:param website:
		:return:
		'''
		try:
			useful_proxies_num = self.proxy_db.llen_useful_proxies(website)
			return useful_proxies_num
		except:
			self.logger.warning('fail get num of {website}_useful_proxies, for fail llen'
			                    .format(website=website), exc_info=True)
			return None

	def get_raw_proxies_num(self):
		''' 获取raw-proxies的数量

		:return:
		'''
		try:
			raw_proxies_num = self.proxy_db.llen_raw_proxies()
			return raw_proxies_num
		except:
			self.logger.warning('fail get num of raw_proxies, for fail llen', exc_info=True)
			return None

	# def get_status(self):
	# 	''' 获取raw-proxies的数量和useful-proxies的数量
	#
	# 	:return:
	# 	'''
	# 	return {
	# 		'raw-proxies': self.get_raw_proxies_num(),
	# 		'useful-proxies': self.get_useful_proxies_num()
	# 	}

	def get_status(self):
		''' 获取raw-proxies的数量和useful-proxies的数量

		:return:
		'''
		status = {
			'raw_proxies': self.get_raw_proxies_num(),
		}

		for website in CHECK_WEBSITES.keys():
			status[self.proxy_db.USEFUL_PROXIES_KEYS[website]] = self.get_useful_proxies_num(website)

		return status

	# def get_all(self):
	# 	''' 获取所有useful-proxies的信息
	#
	# 	:return:
	# 	'''
	# 	useful_proxy_infos = []
	# 	useful_proxies = self.get_all_useful_proxies()
	#
	# 	for useful_proxy in useful_proxies:
	# 		try:
	# 			proxy_info = self.proxy_db.hgetall_proxy(useful_proxy)
	# 		except:
	# 			self.logger.warning('fail get proxy info of {proxy}'
	# 			                    .format(proxy=useful_proxy), exc_info=True)
	# 			proxy_info = {}
	#
	# 		proxy_info['proxy'] = useful_proxy
	# 		useful_proxy_infos.append(proxy_info)
	#
	# 	self.logger.debug('success get all useful proxies\' info')
	# 	return useful_proxy_infos

	# TODO scheme参数未实现

	def get_all(self, website: str):
		''' 获取所有{website}_useful-proxies的信息

		:param website:
		:return:
		'''
		useful_proxy_infos = []
		useful_proxies = self.get_all_useful_proxies(website)

		for useful_proxy in useful_proxies:
			try:
				proxy_info = self.proxy_db.hgetall_proxy(useful_proxy, website)
			except:
				self.logger.warning('fail get proxy info of {website}_{proxy}'
				                    .format(proxy=useful_proxy, website=website), exc_info=True)
				proxy_info = {}

			useful_proxy_infos.append(proxy_info)

		self.logger.debug('success get all {website}_useful_proxies\' info'
		                  .format(website=website))
		return useful_proxy_infos

	# def get_random(self, scheme: str='https'):
	# 	''' 随机获取一个当前可用的proxy
	#
	# 	:return:
	# 	'''
	# 	current_useful_proxies = {}
	# 	useful_proxies = self.get_all_useful_proxies()
	#
	# 	for useful_proxy in useful_proxies:
	# 		try:
	# 			proxy_info = self.proxy_db.hgetall_proxy(useful_proxy)
	# 		except:
	# 			self.logger.warning('fail get proxy info of {proxy}'
	# 			                    .format(proxy=useful_proxy), exc_info=True)
	# 			continue
	#
	# 		# proxy的可用状态
	# 		proxy_state = proxy_info.get('state', 0)
	# 		# proxy的下次可用时间
	# 		proxy_next_get_time = proxy_info.get('next_get_time', time.time())
	#
	# 		if int(proxy_state) == 1 and int(proxy_next_get_time) <= int(time.time()):
	# 			current_useful_proxies[useful_proxy] = proxy_info
	#
	# 	if len(current_useful_proxies.keys()) <= 0:
	# 		self.logger.warning('fail get random useful proxy, for no useful proxy')
	# 		return None
	#
	# 	random_proxy = random.choice(list(current_useful_proxies.keys()))
	# 	random_proxy_info = current_useful_proxies[random_proxy]
	# 	random_proxy_info.update({'proxy': random_proxy})
	# 	proxy_obj = Proxy.from_dict(random_proxy_info)
	# 	# proxy使用后休眠随机时间
	# 	proxy_obj.next_get_time = int(time.time()) + random.randint(PROXY_MIN_SLEEP_TIME, PROXY_MAX_SLEEP_TIME)
	# 	self.update_proxy(proxy_obj)
	#
	# 	return random_proxy

	def get_random(self, website: str, scheme: str='https'):
		''' 随机获取一个当前可用的{website}_proxy

		:param website:
		:param scheme:
		:return:
		'''
		current_useful_proxies = {}
		useful_proxies = self.get_all_useful_proxies(website)

		for useful_proxy in useful_proxies:
			try:
				proxy_info = self.proxy_db.hgetall_proxy(useful_proxy, website)
			except:
				self.logger.warning('fail get proxy info of {website}_{proxy}'
				                    .format(proxy=useful_proxy, website=website), exc_info=True)
				continue

			# proxy的可用状态
			proxy_state = proxy_info.get('state', 0)
			# proxy的下次可用时间
			proxy_next_get_time = proxy_info.get('next_get_time', '') or time.time()

			if int(proxy_state) == 1 and int(proxy_next_get_time) <= int(time.time()):
				current_useful_proxies[useful_proxy] = proxy_info

		if len(current_useful_proxies.keys()) <= 0:
			self.logger.warning('fail get random {website}_useful_proxy, for no useful proxy'
			                    .format(website=website))
			return None

		random_proxy = random.choice(list(current_useful_proxies.keys()))
		random_proxy_info = current_useful_proxies[random_proxy]

		# proxy使用后休眠随机时间
		random_sleep_time = random.randint(CHECK_WEBSITES[website]['min_sleep_time_after_use'],
		                                   CHECK_WEBSITES[website]['max_sleep_time_after_use'])
		random_proxy_info['next_get_time'] = int(time.time()) + random_sleep_time
		self.update_useful_proxy(random_proxy_info, website)

		return random_proxy

	def submit_useless_proxy(self, proxy: str, website: str):
		try:
			if self.proxy_db.exists_proxy(proxy, website):
				proxy_dict = self.proxy_db.hgetall_proxy(proxy, website)
				proxy_dict['state'] = 0
				proxy_dict['fail_counts'] = int(proxy_dict.get('fail_counts'), 0) + 1
				self.update_useful_proxy(proxy_dict, website)
				return True
			else:
				self.logger.debug('{website}_{proxy} was already removed'
				                  .format(website=website, proxy=proxy))
				return False
		except:
			self.logger.warning('fail submit_useless_proxy {website}_{proxy}'
			                    .format(website=website, proxy=proxy), exc_info=True)
			return False