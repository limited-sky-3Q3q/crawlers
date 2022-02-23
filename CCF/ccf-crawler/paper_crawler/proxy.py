# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""requests Get and Post method with proxy module

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    * 实现 PROXY_POOL_ENABLE 的功能，False时代理池应只有本地ip（proxies为None），
    无代理也应该对本地唯一ip做访问频率限制

"""
__author__ = 'lance'


import json
from urllib.parse import urlencode
import requests
from requests import Response
import time
from .mylogger import root, Logger
from .settings import PROXY_API_HOST, PROXY_API_PORT


SUCCESS_CODE = [
	200,
	302
]


class NoUsefulProxyError(Exception):
	def __init__(self):
		super().__init__()

	def __str__(self):
		return repr('no useful proxy')


class PageNotFoundError(Exception):
	def __init__(self):
		super().__init__()

	def __str__(self):
		return repr('page not found')


class HttpStatusCodeError(Exception):
	def __init__(self, response: Response):
		super().__init__(response.status_code, response.text)
		self.http_code = response.status_code
		self.response_text = response.text

	def __str__(self):
		return repr('http status code error, http code: {}'
		            .format(self.http_code))


class NoneUrlError(Exception):
	def __init__(self):
		super(NoneUrlError, self).__init__()

	def __str__(self):
		return repr('None url, please pass correct url')


RANGDOM_GET_PROXY_URL = '{host}:{port}/get_random/'.format(host=PROXY_API_HOST, port=PROXY_API_PORT)
SUBMIT_USELESS_PROXY_URL = '{host}:{port}/submit_useless_proxy/'.format(host=PROXY_API_HOST, port=PROXY_API_PORT)


def _get_random_proxy(website: str)-> str:
	''' 从代理池获取一个针对某个站点的可用代理，若代理池当前无可用代理，抛出NoUsefulProxyError

	:param website:
	:return:
	'''
	url = RANGDOM_GET_PROXY_URL + website
	try:
		response = requests.get(url)
		if response.status_code == 200:
			proxy = response.text
			if not proxy:
				raise NoUsefulProxyError
			return proxy
		else:
			raise HttpStatusCodeError(response)
	except Exception as e:
		raise e

def submit_useless_proxy(proxy: str, website: str):
	''' 提交失效代理

	:param proxy:
	:param website:
	:return:
	'''
	url = SUBMIT_USELESS_PROXY_URL
	params = {
		'proxy': proxy,
		'website': website,
	}

	try:
		requests.get(url, params=params)
	except Exception as e:
		pass

def get_random_proxy(website: str, logger: Logger=root)-> str:
	''' 获取某个针对某个站点的代理, 在代理池服务开启情况下，会直到获取成功

	:param website:
	:param logger:
	:return: 返回可用代理
	'''
	while True:
		try:
			proxy = _get_random_proxy(website)
			logger.debug('success get random proxy {proxy} for {website}'
			             .format(proxy=proxy, website=website))
			return proxy
		except NoUsefulProxyError:
			logger.debug('no useful proxy for {website}, sleep {sleep_time}s get again'
			             .format(website=website, sleep_time=3))
			time.sleep(3)

def _requests_with_proxy(method: str, url: str, proxy: str,
                         timeout: int=30, **kwargs)-> Response:
	if url == '':
		raise NoneUrlError
	# print(url)
	METHODS = {
		'get': requests.get,
		'post': requests.post,
	}
	proxies = {
		'http': 'http://{proxy}'.format(proxy=proxy),
		'https': 'https://{proxy}'.format(proxy=proxy),
	}

	requests_method = METHODS[method]
	try:
		response = requests_method(url, proxies=proxies, timeout=timeout, **kwargs)
		if response.status_code in SUCCESS_CODE:
			return response
		elif response.status_code == 404:
			raise PageNotFoundError
		else:
			raise HttpStatusCodeError(response)
	except Exception as e:
		raise e

# FIXME 暂时10次重试机会
def requests_get_with_proxy(url: str, *, website: str, timeout: int=30,
                            logger: Logger=root, **kwargs)-> Response or None:
	''' 使用代理执行requests get请求，除非页面不存在，会一直更换代理直到请求成功

	:param url:
	:param website:
	:param timeout:
	:param logger:
	:param kwargs:
	:return:
	'''
	page_url = (url + '?' + urlencode(kwargs['params'])) if 'params' in kwargs else url
	times = 10
	while times >= 0:
		proxy = get_random_proxy(website, logger)
		try:
			logger.debug('getting {page_url} with {website} proxy {proxy}'
			             .format(page_url=page_url, website=website, proxy=proxy))
			response = _requests_with_proxy('get', url, proxy, timeout=timeout, **kwargs)
			logger.info('[SUCCESS] get {page_url}'
			            .format(page_url=page_url))
			return response
		except NoneUrlError:
			logger.warning('[FAIL] get {page_url}, for url is None'
			               .format(page_url=page_url), exc_info=True)
			return NoneUrlError
		except PageNotFoundError:
			logger.warning('[FAIL] get {page_url}, for page is not exists'
			               .format(page_url=page_url), exc_info=True)
			return None
		except:
			logger.debug('useless proxy {website}_{proxy}'
			             .format(website=website, proxy=proxy), exc_info=True)
			submit_useless_proxy(proxy, website)

		times -= 1

# FIXME 暂时10次重试机会
def requests_post_with_proxy(url: str, *, website: str, timeout: int=30,
                             logger: Logger=root, **kwargs)-> Response or None:
	''' 使用代理执行requests post请求

	:param url:
	:param website:
	:param timeout:
	:param logger:
	:param kwargs:
	:return:
	'''
	times = 10
	while times >= 0:
		proxy = get_random_proxy(website, logger=logger)
		try:
			logger.debug('postting {url} with {website} proxy {proxy}, json={json}, data={data}'
			             .format(url=url, website=website, proxy=proxy,
			                     json=json.dumps(kwargs.get('json', {})),
			                     data=json.dumps(kwargs.get('data', {}))))
			response = _requests_with_proxy('post', url, proxy, timeout=timeout, **kwargs)
			logger.info('[SUCCESS] post {url}, json={json}, data={data}'
			            .format(url=url,
			                    json=json.dumps(kwargs.get('json', {})),
			                    data=json.dumps(kwargs.get('data', {}))))
			return response
		except NoneUrlError:
			logger.warning('[FAIL] post {url}, json={json}, data={data}, for url is None'
			               .format(url=url,
			                    json=json.dumps(kwargs.get('json', {})),
			                    data=json.dumps(kwargs.get('data', {}))), exc_info=True)
			return None
		except PageNotFoundError:
			logger.warning('[FAIL] post {url}, json={json}, data={data}, for page is not exists'
			               .format(url=url,
			                    json=json.dumps(kwargs.get('json', {})),
			                    data=json.dumps(kwargs.get('data', {}))), exc_info=True)
			return None
		except:
			logger.debug('useless proxy {website}_{proxy}'
			             .format(website=website, proxy=proxy), exc_info=True)
			submit_useless_proxy(proxy, website)

		times -= 1


class ProxySession():
	def __init__(self, website: str, logger: Logger=root):
		self.website = website
		self.logger = logger
		self.session = requests.Session()
		self.proxy = ''
		# self.proxies = {}

		self._set_proxies()

	def _set_proxies(self):
		self.proxy = get_random_proxy(self.website)
		self.session.proxies = {
			'http': 'http://{proxy}'.format(proxy=self.proxy),
			'https': 'https://{proxy}'.format(proxy=self.proxy),
		}

	def _session_request_with_proxy(self, method: str, url: str,
	                                timeout: int=30, **kwargs)-> Response:
		if url == '':
			raise NoneUrlError

		METHODS = {
			'get': self.session.get,
			'post': self.session.post,
		}

		requests_method = METHODS[method]
		try:
			response = requests_method(url, timeout=timeout, **kwargs)
			if response.status_code in SUCCESS_CODE:
				return response
			elif response.status_code == 404:
				raise PageNotFoundError
			else:
				raise HttpStatusCodeError(response)
		except Exception as e:
			raise e

	def get(self, url: str, timeout: int=30, **kwargs)-> Response or None:
		'''

		:param url:
		:param timeout:
		:param kwargs:
		:return:
		'''
		page_url = (url + '?' + urlencode(kwargs['params'])) if 'params' in kwargs else url
		while True:
			try:
				self.logger.debug('session_get {page_url} with {website} proxy {proxy}'
				             .format(page_url=page_url, website=self.website, proxy=self.proxy))
				response = self._session_request_with_proxy('get', url, timeout=timeout, **kwargs)
				self.logger.info('[SUCCESS] session_get {page_url}'
				                 .format(page_url=page_url))
				return response
			except NoneUrlError:
				self.logger.warning('[FAIL] session_get {page_url}, for url is None'
				                    .format(page_url=page_url), exc_info=True)
				return None
			except PageNotFoundError:
				self.logger.warning('[FAIL] session_get {page_url}, for page is not exists'
				                    .format(page_url=page_url), exc_info=True)
				return None
			except:
				self.logger.debug('useless proxy {website}_{proxy}'
				             .format(website=self.website, proxy=self.proxy), exc_info=True)
				submit_useless_proxy(self.proxy, self.website)
				self._set_proxies()

	def post(self, url: str, timeout: int=30, **kwargs)-> Response or None:
		'''

		:param url:
		:param timeout:
		:param kwargs:
		:return:
		'''
		while True:
			try:
				self.logger.debug('session_post {url} with {website} proxy {proxy}, json={json}, data={data}'
			             .format(url=url, website=self.website, proxy=self.proxy,
			                     json=json.dumps(kwargs.get('json', {})),
			                     data=json.dumps(kwargs.get('data', {}))))
				response = self._session_request_with_proxy('post', url, timeout=timeout, **kwargs)
				self.logger.info('[SUCCESS] session_post {url}, json={json}, data={data}'
				                 .format(url=url,
			                     json=json.dumps(kwargs.get('json', {})),
			                     data=json.dumps(kwargs.get('data', {}))))
				return response
			except NoneUrlError:
				self.logger.warning('[FAIL] post {url}, for url is None'
				                    .format(url=url), exc_info=True)
				return None
			except PageNotFoundError:
				self.logger.warning('[FAIL] session_post {url}, json={json}, data={data}, for page is not exists'
				                    .format(url=url,
				                            json=json.dumps(kwargs.get('json', {})),
				                            data=json.dumps(kwargs.get('data', {}))), exc_info=True)
				return None
			except:
				self.logger.debug('useless proxy {website}_{proxy}'
				             .format(website=self.website, proxy=self.proxy), exc_info=True)
				submit_useless_proxy(self.proxy, self.website)
				self._set_proxies()


if __name__ == '__main__':
	# url = 'https://ieeexplore.ieee.org/document/8712389'
	# url = 'https://httpbin.org/get?show_env=1'
	url = 'https://dl.acm.org/profile/81351604771'
	website = 'acm'
	headers = {
		'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
		'Content-Type': 'application/json'
	}

	def test_get():
		response = requests_get_with_proxy(url, website, headers=headers, timeout=15)
		print(response.text)

	def test_post():
		print(__search('Area efficient asynchronous SDM routers using 2-stage Clos switches', 'title'))

	def __search(search_term, search_type=None, rows_per_page=25, logger: Logger=root):
		'''

		:param type: [title, authors, author_ids, index_terms] (paper标题、作者、作者id、关键词)
		:param search_term: 搜索文本
		:param rows_per_page: 一次搜索结果数
		:param logger:
		:return:
		'''
		search_term = search_term.strip()
		if search_type == 'index_terms':
			query_text = '"Index Terms":{0}'.format(search_term)
		elif search_type == 'title':
			query_text = '("Document Title":{0})'.format(search_term)
		elif search_type == 'authors':
			query_text = '("Authors":{0})'.format(search_term)
		elif search_type == 'author_ids':
			text = '"Author Ids":{0}'.format(search_term)
			query_text = [text]
		else:
			query_text = search_term

		base_url = 'https://ieeexplore.ieee.org/rest/search'
		headers = {
			'Host': 'ieeexplore.ieee.org',
			'Origin': 'https://ieeexplore.ieee.org',
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
			# 'Content-Type': 'application/json',
		}

		jsonData = {
			'highline': True,
			'newsearch': True,
			'queryText': query_text,
			'returnType': 'SEARCH',
			'returnFacets': ['ALL'],
			'rowsPerPage': rows_per_page
		}

		response = requests_post_with_proxy(base_url, website='ieee', headers=headers, json=jsonData, logger=logger)
		if response == None:
			logger.warning('[IEEE_SEARCH_FAIL] with query_text <{query_text}>, for network error'
			               .format(query_text=query_text))
			return None

		try:
			results = response.json()
		except:
			logger.warning('[IEEE_SEARCH_FAIL] with query_text <{query_text}>, for json error'
			               .format(query_text=query_text))
			return None

		if not (('records' in results) and (len(results['records']) > 0)):
			logger.warning('[IEEE_SEARCH_FAIL] with query_text <{query_text}>, for no result'
			               .format(query_text=query_text))
			return None

		return results['records']

	def test_session_get():
		proxy_session = ProxySession('acm')
		# url = 'https://httpbin.org/get?show_env=1'
		urls = [
			'https://dl.acm.org/profile/81351604771',
			'https://dl.acm.org/profile/81337487753',
			'https://dl.acm.org/profile/81100512314',
		]
		for url in urls:
			response = proxy_session.get(url)
			print(response.status_code)

	def test_session_post():
		proxy_session = ProxySession('ieee')
		url = 'https://httpbin.org/post'
		for _ in range(3):
			response = proxy_session.post(url)
			print(response.text)

	# test_get()
	# test_post()
	# test_session_get()
	# test_session_post()

	from threading import Thread
	ths = []
	for _ in range(20):
		th = Thread(target=test_post)
		th.start()
		ths.append(th)

	for th in ths:
		th.join()
