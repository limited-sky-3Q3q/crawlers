import time
import json
import requests
import asyncio
import aiohttp

from src.utils import random_user_agent
from src.mylogger import root, Logger
from src.settings import HTTPBIN_URL


class RawProxy():
	def __init__(self, proxy: str, scheme: str, address: str, source: str, access_time: str):
		'''

		:param proxy:
		:param scheme: (http, https)
		:param address: 代理地址
		:param source: 代理来源
		:param access_time: 代理获取时间
		'''
		self.proxy = proxy
		self.scheme = scheme
		self.address = address
		self.source = source
		self.access_time = access_time

	def to_dict(self):
		return {
			'proxy': self.proxy,
			'scheme': self.scheme,
			'address': self.address,
			'source': self.source,
			'access_time': self.access_time
		}

	def to_json(self):
		return json.dumps(self.to_dict())


class UsefulProxy(RawProxy):
	def __init__(self, raw_proxy_dict: dict, website: str, state: int=0, next_get_time: int or str='',
	             last_check_time: str='', fail_counts: int=0, check_counts: int=0):
		super().__init__(**raw_proxy_dict)
		self.website = website
		self.state = state
		self.next_get_time = next_get_time
		self.last_check_time = last_check_time
		self.fail_counts = fail_counts
		self.check_counts = check_counts
		
	def to_dict(self):
		return {
			'proxy': self.proxy,
			'scheme': self.scheme,
			'address': self.address,
			'source': self.source,
			'access_time': self.access_time,
			'website': self.website,
			'state': self.state,
			'next_get_time': self.next_get_time,
			'fail_counts': self.fail_counts,
			'last_check_time': self.last_check_time,
			'check_counts': self.check_counts
		}


class Proxy():
	def __init__(self, proxy: str, scheme: str, address: str, source: str, access_time: str, state: int=0,
	             next_get_time: int or str='', last_check_time: str='', fail_counts: int=0, check_counts: int=0):
		'''

		:param proxy: {ip}:{port}
		:param scheme: (http, https)
		:param address: 代理地址
		:param source: 代理来源
		:param access_time: 代理获取时间
		:param state: 0/1 代理当前可用状态，0为不可用，1为可用
		:param next_get_time: 下次可用时间，值为unix时间戳
		:param last_check_time: 上次检验代理可用性时间
		:param fail_counts: 检验代理失败次数
		:param check_counts: 代理检验次数
		'''
		self.__proxy = proxy
		self.__scheme = scheme.lower()
		self.__address = address
		self.__source = source
		self.__access_time = access_time

		self.state = state
		self.next_get_time = next_get_time
		self.last_check_time = last_check_time
		self.fail_counts = fail_counts
		self.check_counts = check_counts

	@property
	def proxy(self):
		return self.__proxy

	@property
	def scheme(self):
		return self.__scheme

	@property
	def address(self):
		return self.__address

	@property
	def source(self):
		return self.__source

	@property
	def access_time(self):
		return self.__access_time

	@classmethod
	def check_usability(cls, proxy: str, website_url: str)-> bool:
		proxies = {
			'http': 'http://{proxy}'.format(proxy=proxy),
			'https': 'https://{proxy}'.format(proxy=proxy),
		}
		headers = {
			'User-Agent': random_user_agent(),
		}
		try:
			response = requests.get(website_url, headers=headers, proxies=proxies, timeout=15)
			if response.status_code == 200:
				return True
		except:
			return False

		return False

	# 不能将HTTPBIN部署在本地上来执行测试，可以将httpbin部署到自己的服务器上
	@classmethod
	def check_high_anonymity(cls, proxy: str)-> bool:
		proxies = {
			'http': 'http://{proxy}'.format(proxy=proxy),
			'https': 'https://{proxy}'.format(proxy=proxy),
		}
		headers = {
			'User-Agent': random_user_agent(),
		}
		try:
			response = requests.get(HTTPBIN_URL, headers=headers, proxies=proxies, timeout=15)
			if response.status_code == 200 and response.json()['origin'] == proxy.split(':')[0]:
				return True
		except:
			return False

		return False

	@classmethod
	# TODO 虽然aiohttp只能用http代理，但是一样可也检测https代理
	async def check_usability_async(cls, proxy: str, website_url: str):
		proxy = {
			'http': 'http://{proxy}'.format(proxy=proxy),
		}
		headers = {
			'User-Agent': random_user_agent(),
		}
		async with aiohttp.ClientSession() as session:
			try:
				async with session.get(website_url, headers=headers, proxy=proxy, timeout=15) as response:
					if response.status == 200:
						return True
			except:
				return False

		return False

	def to_dict(self):
		return {
			'proxy': self.proxy,
			'scheme': self.scheme,
			'address': self.address,
			'source': self.source,
			'access_time': self.access_time,
			'state': self.state,
			'next_get_time': self.next_get_time,
			'fail_counts': self.fail_counts,
			'last_check_time': self.last_check_time,
			'check_counts': self.check_counts
		}

	@classmethod
	def from_dict(cls, proxy_dict):
		return cls(proxy_dict.get('proxy', ''),
		           proxy_dict.get('scheme', ''),
		           proxy_dict.get('address', ''),
		           proxy_dict.get('source', ''),
		           proxy_dict.get('access_time', ''),
		           int(proxy_dict.get('state', 0)),
		           proxy_dict.get('next_get_time', ''),
		           proxy_dict.get('last_check_time', ''),
		           int(proxy_dict.get('fail_counts', 0)),
		           int(proxy_dict.get('check_counts', 0)))