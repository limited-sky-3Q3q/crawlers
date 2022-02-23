import redis

from .settings import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, CHECK_WEBSITES
from .utils import singleton
from .error import UnknowWebsiteError


@singleton
class ProxyDB():
	# 刚获取的proxy队列
	RAW_PROXIES_KEY = 'raw_proxies'

	USEFUL_PROXIES_KEY = 'useful_proxies'
	CHECK_USEFUL_PROXIES_KEY = 'check_useful_proxies'

	USEFUL_PROXIES_KEYS = {}
	CHECK_USEFUL_PROXIES_KEYS = {}

	def __init__(self, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=0, decode_responses=True):
		'''

		:param host:
		:param port:
		:param password:
		:param db:
		:param decode_responses:
		'''
		for website in CHECK_WEBSITES.keys():
			self.USEFUL_PROXIES_KEYS[website] = '{website}_useful_proxies'.format(website=website)
			self.CHECK_USEFUL_PROXIES_KEYS[website] = '{website}_check_useful_proxies'.format(website=website)

		pool = redis.ConnectionPool(host=host, port=port, password=password, db=db, decode_responses=decode_responses)
		self.db = redis.StrictRedis(connection_pool=pool)
		self.db.flushdb()

	# def exists_proxy(self, proxy: str):
	# 	''' 判断一个proxy是否存在
	#
	# 	:param proxy:
	# 	:return:
	# 	'''
	# 	try:
	# 		return self.db.exists(proxy)
	# 	except Exception as e:
	# 		raise e

	def generate_useful_proxy_key(self, proxy: str, website: str):
		''' 根据proxy和website生成存储useful proxy的信息的键名

		:param proxy:
		:param website:
		:return:
		'''
		if website not in CHECK_WEBSITES.keys():
			raise UnknowWebsiteError

		return '{website}_{proxy}'.format(website=website, proxy=proxy)

	def exists_proxy(self, proxy: str, website: str=''):
		''' 判断一个proxy是否存在

		:param proxy:
		:param website:
		:return:
		'''
		if website:
			proxy_key = self.generate_useful_proxy_key(proxy, website)
		else:
			proxy_key = proxy

		try:
			return self.db.exists(proxy_key)
		except Exception as e:
			raise e

	# def hgetall_proxy(self, proxy: str):
	# 	''' 获取一个proxy的信息
	#
	# 	:param proxy:
	# 	:return:
	# 	'''
	# 	try:
	# 		return self.db.hgetall(proxy)
	# 	except Exception as e:
	# 		raise e

	def hgetall_proxy(self, proxy: str, website: str=''):
		''' 获取一个proxy的信息

		:param proxy:
		:param website:
		:return:
		'''
		if website:
			proxy_key = self.generate_useful_proxy_key(proxy, website)
		else:
			proxy_key = proxy

		try:
			return self.db.hgetall(proxy_key)
		except Exception as e:
			raise e

	# def hmset_proxy(self, proxy: str, proxy_dict: dict):
	# 	''' 存入一个proxy的信息
	#
	# 	:param proxy:
	# 	:param proxy_dict:
	# 	:return:
	# 	'''
	# 	# 删掉空值
	# 	try:
	# 		del_keys = []
	# 		for (key, value) in proxy_dict.items():
	# 			if value == '' or value == None:
	# 				del_keys.append(key)
	#
	# 		for del_key in del_keys:
	# 			del proxy_dict[del_key]
	#
	# 		return self.db.hmset(proxy, proxy_dict)
	# 	except Exception as e:
	# 		raise e

	def hmset_proxy(self, proxy: str, proxy_dict: dict, website: str=''):
		''' 存入一个proxy的信息

		:param proxy:
		:param proxy_dict:
		:param website:
		:return:
		'''
		if website:
			proxy_key = self.generate_useful_proxy_key(proxy, website)
		else:
			proxy_key = proxy

		try:
			return self.db.hmset(proxy_key, proxy_dict)
		except Exception as e:
			raise e

	# TODO 未使用
	def hset_proxy(self, proxy: str, key: str, value: str):
		''' 修改proxy的某项属性

		:param proxy:
		:param key:
		:param value:
		:return:
		'''
		try:
			return self.db.hset(proxy, key, value)
		except Exception as e:
			raise e

	def del_proxy(self, proxy: str):
		''' 删除一个proxy

		:param proxy:
		:return:
		'''
		try:
			return self.db.delete(proxy)
		except Exception as e:
			raise e

	# def del_useful_proxy(self, useful_proxy: str):
	# 	''' 删除一个可用的proxy，包括从useful_proxies列表中删除和del_proxy
	#
	# 	:param useful_proxy:
	# 	:return:
	# 	'''
	# 	try:
	# 		self.db.lrem(self.USEFUL_PROXIES_KEY, 0, useful_proxy)
	# 		self.del_proxy(useful_proxy)
	# 	except Exception as e:
	# 		raise e
	# 	return True

	def del_useful_proxy(self, useful_proxy: str, website: str):
		''' 删除一个可用的proxy，包括从{website}_useful_proxies列表中删除和del_proxy

		:param useful_proxy:
		:param website:
		:return:
		'''
		proxy_key = self.generate_useful_proxy_key(useful_proxy, website)

		try:
			self.db.lrem(self.USEFUL_PROXIES_KEYS[website], 0, useful_proxy)
			self.del_proxy(proxy_key)
		except Exception as e:
			raise e
		return True

	def lpop_raw_proxy(self):
		''' 从raw_proxies列表头部弹出一个proxy

		:return:
		'''
		try:
			return self.db.lpop(self.RAW_PROXIES_KEY)
		except Exception as e:
			raise e

	def blpop_raw_proxy(self, timeout: int=0):
		''' 阻塞式从raw_proxies列表头部弹出一个proxy

		:param timeout: 阻塞超时时间
		:return: tuple ('raw_proxies', proxy)
		'''
		try:
			return self.db.blpop(self.RAW_PROXIES_KEY, timeout=timeout)
		except Exception as e:
			raise e

	# def blpop_check_useful_proxy(self, timeout: int=0):
	# 	''' 阻塞式从check_useful_proxies列表头部弹出一个proxy
	#
	# 	:param timeout: 阻塞超时时间
	# 	:return: tuple ('raw_proxies', proxy)
	# 	'''
	# 	try:
	# 		return self.db.blpop(self.CHECK_USEFUL_PROXIES_KEY, timeout=timeout)
	# 	except Exception as e:
	# 		raise e

	def blpop_check_useful_proxy(self, website: str, timeout: int=0):
		''' 阻塞式从check_useful_proxies列表头部弹出一个proxy

		:param website:
		:param timeout: 阻塞超时时间
		:return: tuple ('{website}_useful_proxies', proxy)
		'''
		if website not in CHECK_WEBSITES.keys():
			raise UnknowWebsiteError

		try:
			return self.db.blpop(self.CHECK_USEFUL_PROXIES_KEYS[website], timeout=timeout)
		except Exception as e:
			raise e

	def rpush_raw_proxy(self, *proxies):
		''' 往raw_proxies列表尾部插入一个proxy

		:param proxy:
		:return:
		'''
		try:
			return self.db.rpush(self.RAW_PROXIES_KEY, *proxies)
		except Exception as e:
			raise e

	# def rpush_useful_proxy(self, *proxies):
	# 	''' 往useful_proxies列表尾部插入一个useful_proxy
	#
	# 	:param proxy:
	# 	:return:
	# 	'''
	# 	try:
	# 		return self.db.rpush(self.USEFUL_PROXIES_KEY, *proxies)
	# 	except Exception as e:
	# 		raise e

	def rpush_useful_proxy(self, website: str, *proxies):
		''' 往{website}_useful_proxies列表尾部插入一个useful_proxy

		:param website:
		:param proxy:
		:return:
		'''
		if website not in CHECK_WEBSITES.keys():
			raise UnknowWebsiteError

		try:
			return self.db.rpush(self.USEFUL_PROXIES_KEYS[website], *proxies)
		except Exception as e:
			raise e

	# def rpush_check_useful_proxy(self, *proxies):
	# 	''' 往check_useful_proxies列表尾部插入一个待检测的useful_proxy
	#
	# 	:param proxy:
	# 	:return:
	# 	'''
	# 	try:
	# 		return self.db.rpush(self.CHECK_USEFUL_PROXIES_KEY, *proxies)
	# 	except Exception as e:
	# 		raise e

	def rpush_check_useful_proxy(self, website: str, *proxies):
		''' 往{website}_check_useful_proxies列表尾部插入一个待检测的useful_proxy

		:param website:
		:param proxy:
		:return:
		'''
		if website not in CHECK_WEBSITES.keys():
			raise UnknowWebsiteError

		try:
			return self.db.rpush(self.CHECK_USEFUL_PROXIES_KEYS[website], *proxies)
		except Exception as e:
			raise e

	# def llen_useful_proxies(self):
	# 	''' 获取useful_proxies列表的长度
	#
	# 	:return:
	# 	'''
	# 	try:
	# 		return self.db.llen(self.USEFUL_PROXIES_KEY)
	# 	except Exception as e:
	# 		raise e

	def llen_useful_proxies(self, website: str):
		''' 获取useful_proxies列表的长度

		:param website
		:return:
		'''
		if website not in CHECK_WEBSITES.keys():
			raise UnknowWebsiteError

		try:
			return self.db.llen(self.USEFUL_PROXIES_KEYS[website])
		except Exception as e:
			raise e

	def llen_raw_proxies(self):
		''' 获取raw proxies列表的长度

		:return:
		'''
		try:
			return self.db.llen(self.RAW_PROXIES_KEY)
		except Exception as e:
			raise e

	# def lrange_useful_proxies(self, start: int, end: int):
	# 	''' 范围获取useful_proxies, [start, end]
	#
	# 	:return:
	# 	'''
	# 	try:
	# 		return self.db.lrange(self.USEFUL_PROXIES_KEY, start, end)
	# 	except Exception as e:
	# 		raise e

	def lrange_useful_proxies(self, website: str, start: int, end: int):
		''' 范围获取useful_proxies, [start, end]

		:param website:
		:param start:
		:param end:
		:return:
		'''
		if website not in CHECK_WEBSITES.keys():
			raise UnknowWebsiteError

		try:
			return self.db.lrange(self.USEFUL_PROXIES_KEYS[website], start, end)
		except Exception as e:
			raise e