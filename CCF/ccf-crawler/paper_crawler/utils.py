import requests
import random
import time
import os
from lxml import etree
from urllib.parse import urlencode
from functools import wraps, partial
import shutil
import re

from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.parse import urlunparse
from posixpath import normpath

from .mylogger import root, Logger


def random_user_agent():
	user_agents = [
		# Windows10 / Chrome 75.0.3770.142
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
		# Windows10 / Firefox 69.0b15
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
		# Windows10 / Opera 63.0.3368.43
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36 OPR/63.0.3368.43',
		# Windows10 / Edge 44.18362.1.0
		'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362',
		# Windows10 / IE 11.10000.18362.0
		'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; LCTE; rv:11.0) like Gecko',
		# Windows10 x64 / Safari 5.1.4（7534.54.16）
		'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/534.54.16 (KHTML, like Gecko) Version/5.1.4 Safari/534.54.16',
		# Windows10 / QQ浏览器 10.5（3739）
		'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3722.400 QQBrowser/10.5.3739.400',
		# Windows10 / 360安全浏览器 10.0.1977.0
		'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE',
		# Windows10 / 360极速浏览器 11.0.2179.0
		'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36 QIHU 360EE',
		# Windows10 / UC浏览器 6.2.3964.2
		'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.3964.2 Safari/537.36',
		# Windows10 / 搜狗浏览器 8.5.10.31270
		'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
		# Windows10 / 猎豹浏览器 6.5.115.19331.8001
		'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36 LBBROWSER',
		# Windows10 / 傲游浏览器 5.2.7.5000
		'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
		# Windows10 / 2345加速浏览器 10.1.0.19399
		'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3947.100 Safari/537.36',

		# Android / Chrome 76.0.3809.111
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.111 Mobile Safari/537.36',
		# Android / Firefox 68.0.2
		'Mozilla/5.0 (Android 7.1.1; Mobile; rv:68.0) Gecko/68.0 Firefox/68.0',
		# Android / Opera 53.0.2569.141117
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk Build/NMF26F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Mobile Safari/537.36 OPR/53.0.2569.141117',
		# Android / Edge 42.0.2.3819
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.90 Mobile Safari/537.36 EdgA/42.0.2.3819',
		# Android / QQ浏览器 9.6.1.5190
		'Mozilla/5.0 (Linux; U; Android 7.1.1; zh-cn; OPPO R9sk Build/NMF26F) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/66.0.3359.126 MQQBrowser/9.6 Mobile Safari/537.36',
		# Android / OPPO浏览器 10.5.1.2_2c91537
		'Mozilla/5.0 (Linux; U; Android 7.1.1; zh-cn; OPPO R9sk Build/NMF26F) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.80 Mobile Safari/537.36 OppoBrowser/10.5.1.2',
		# Android / 360浏览器 8.2.0.162
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/62.0.3202.97 Mobile Safari/537.36',
		# Android / 360极速浏览器 1.0.100.1078
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk Build/NMF26F) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.80 Mobile Safari/537.36 360 Alitephone Browser (1.5.0.90/1.0.100.1078) mso_sdk(1.0.0)',
		# Android / UC浏览器 12.6.0.1040
		'Mozilla/5.0 (Linux; U; Android 7.1.1; zh-CN; OPPO R9sk Build/NMF26F) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.108 UCBrowser/12.6.0.1040 Mobile Safari/537.36',
		# Android / 猎豹浏览器 5.12.3
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.80 Mobile Safari/537.36 LieBaoFast/5.12.3',
		# Android / 百度浏览器 7.19
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/48.0.2564.116 Mobile Safari/537.36 T7/9.1 baidubrowser/7.19.13.0 (Baidu; P1 7.1.1)',
		# Android / 搜狗浏览器 5.22.8.71677
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/68.0.3440.106 Mobile Safari/537.36 AWP/2.0 SogouMSE,SogouMobileBrowser/5.22.8',
		# Android / 2345浏览器 11.0.1
		'Mozilla/5.0 (Linux; Android 7.1.1; OPPO R9sk Build/NMF26F; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.80 Mobile Safari/537.36 Mb2345Browser/11.0.1',

		# iPhone3
		'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/1A542a Safari/419.3',
		# iPhone4
		'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7',
		# iPhone6s
		'Mozilla/5.0 (iPhone 6s; CPU iPhone OS 11_4_1 like Mac OS X) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0 MQQBrowser/8.3.0 Mobile/15B87 Safari/604.1 MttCustomUA/2 QBWebViewType/1 WKType/1',
		# iPad
		'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10',
		# iPod
		'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5',
		# BlackBerry
		'Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+',
		# WebOS HP Touchpad
		'Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0',
		# Nokia N97
		'Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124',
		# Windows Phone Mango
		'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)',

		'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
        'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
	]
	return random.choice(user_agents)
	# return 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'


def url_join(base, url):
	''' url拼接

	:param base:
	:param url:
	:return:
	'''
	url1 = urljoin(base, url)
	arr = urlparse(url1)
	path = normpath(arr[2])
	return urlunparse((arr.scheme, arr.netloc, path, arr.params, arr.query, arr.fragment))


def find_all(substr, string):
	''' 找出给定字符串中匹配的所有子串的开头位置

	:param substr:
	:param string:
	:return:
	'''
	return [i.start() for i in re.finditer(substr, string)]


def args2str(args: list or tuple, kwargs: dict) -> str:
	''' args列表和kwargs字典参数转换成字符串

	:param args:
	:param kwargs:
	:return:
	'''
	args = args if isinstance(args, list) or isinstance(args, tuple) else []
	kwargs = kwargs if isinstance(kwargs, dict) else dict()

	args_str = ', '.join(['\'{value}\''.format(value=str(value)) if isinstance(value, str) else str(value)
						 for value in args])
	args_str = args_str if args_str else ''
	kwargs_str = ', '.join([key + '=' + ('\'{value}\''.format(value=str(value)) if isinstance(value, str) else str(value))
							for key, value in kwargs.items()])
	args_str = args_str + (', ' if args_str else '') + kwargs_str if kwargs_str else args_str
	return args_str


def decode_email(email):
	''' 解码Cloudflare对邮箱的加密，解码过程中发生错误会抛出异常

	:param email:
	:return:
	'''
	def from_char_code(char_codes):
		if not (type(char_codes) == list or type(char_codes) == set):
			char_codes = [char_codes]

		return ''.join(map(chr, char_codes))

	charcodes = email.split('/cdn-cgi/l/email-protection#')[-1]
	# print(charcodes)
	email = ''
	try:
		a = int(charcodes[0 : 2], 16)
		for i in range(2, len(charcodes), 2):
			l = int(charcodes[i : i+2], 16) ^ a
			email += from_char_code(l)
	except Exception as e:
		raise e

	return email


# FIXME exceptions可选处理异常，目前只接受Exception
def retry(tries: int=3, exceptions: list or Exception=Exception, fail_result=None,
		  wait_random_min: int=60, wait_random_max: int=100, logger: Logger=root):
	''' 重试装饰器

	:param tries: 最大执行次数
	:param exceptions: 需要处理的异常(列表)
	:param fail_result: 重试后仍失败的返回值
	:param wait_random_min: 重试时随机等待的最小时间
	:param wait_random_max: 重试时随机等待的最大时间
	:param logger:
	:return:
	'''
	tries = tries if tries > 0 else 3

	def decorator(func):

		@wraps(func)
		def wrapper(*args, **kwargs):
			nonlocal tries
			while tries:
				tries -= 1
				try:
					return func(*args, **kwargs)
				except exceptions as e:
					wait_time = random.randint(wait_random_min, wait_random_max)
					args_str = args2str(args, kwargs)
					logger.warning('{e}\nretrying {func}({args_str}) in {wait_time} seconds...'.format(e=e, func=func.__name__, args_str=args_str, wait_time=wait_time))
					time.sleep(wait_time)
			return fail_result

		return wrapper

	return decorator


# FIXME exceptions可选处理异常，目前只接受Exception
def retry_call(func, fargs: list or tuple=None, fkwargs: dict=None, tries: int=3, exceptions=Exception,
			   fail_result=None, wait_random_min: int=10, wait_random_max: int=30,logger: Logger=root):
	''' retry

	:param func: 需要重试的函数
	:param fargs: 传入func的参数
	:param fkwargs: 传入func的参数
	:param tries: 最大执行次数
	:param exceptions: 需要处理的异常(列表)
	:param fail_result: 重试后仍失败的返回值
	:param wait_random_min: 重试时随机等待的最小时间
	:param wait_random_max: 重试时随机等待的最大时间
	:param logger:
	:return:
	'''
	tries = tries if tries > 0 else 3

	args = fargs if fargs else list()
	kwargs = fkwargs if fkwargs else dict()

	while tries:
		tries -= 1
		try:
			return func(*args, **kwargs)
		except exceptions as e:
			wait_time = random.randint(wait_random_min, wait_random_max)
			args_str = args2str(args, kwargs)
			logger.warning('{e}\nretrying {func}({args_str}) in {wait_time} seconds...'.format(e=e, func=func.__name__, args_str=args_str, wait_time=wait_time))
			time.sleep(wait_time)
	return fail_result


def requests_get(url: str, *, tries: int=3, success_wait: int=0, logger: Logger=root,
                 wait_random_min: int=10, wait_random_max: int=30, **kwargs):
	""" 封装requests的get请求, 失败可重试请求

	:param url: 需请求的地址
	:param tries: 最大请求尝试次数
	:param success_wait: 请求成功时暂停多久，默认为0（主要为了应对ACM网站）
	:param logger:
	:param wait_random_min: 重试请求时随机等待的最小时间
	:param wait_random_max: 重试请求时随机等待的最大时间
    :param \*\*kwargs: Optional arguments that ``request`` takes.
	:return: 请求成功返回response对象，失败返回None
	"""

	if url == '' or url == None:
		logger.warning('[FAIL] to excute requests_get, the url parameter passed is None')
		return None

	pageURL = (url + '?' + urlencode(kwargs['params'])) if 'params' in kwargs else url

	def _get(url: str, **kwargs):
		nonlocal pageURL
		logger.debug('[...] [GET] {0}'.format(pageURL))
		response = requests.get(url, **kwargs)
		return response

	fkwargs = {
		'url': url,
	}
	fkwargs.update(kwargs)
	response = retry_call(_get,
	                      fkwargs=fkwargs,
						  tries=tries,
						  fail_result=None,
						  wait_random_min=wait_random_min,
						  wait_random_max=wait_random_max,
						  logger=logger)

	if response == None:
		logger.warning('[FAIL] [GET] {url}'.format(url=pageURL))
		return None

	#请求成功，但是状态码不是200
	if response.status_code != 200:
		logger.warning('[FAIL] [GET] {url}, for http status: {status_code}'.format(url=pageURL, status_code=response.status_code))
		return None

	# 成功获取到页面，返回response
	logger.info('[SUCCESS] [get] {url}'.format(url=pageURL))
	# 请求成功后暂停
	logger.debug('[WAIT] {}s'
	             .format(success_wait))
	time.sleep(success_wait)
	return response


def requests_post(url: str, *, tries: int=3, success_wait: int=0, logger: Logger=root,
                  wait_random_min: int=10, wait_random_max: int=30, **kwargs):
	""" 封装requests的get请求，失败可重试请求

	:param url: 需请求的地址
	:param tries: 最大请求尝试次数
	:param success_wait: 成功后暂停时间，默认为0
	:param logger:
	:param wait_random_min: 重试时随机等待最小时间
	:param wait_random_max: 重试时随机等待最大时间
    :param \*\*kwargs: Optional arguments that ``request`` takes.
	:return: 请求成功返回response对象，失败返回None
	"""

	if url == '' or url == None:
		logger.warning('[FAIL] to excute requests_post, the url parameter passed is None')
		return None

	def _post(url: str, **kwargs):
		logger.debug('[...] [POST] {url}'.format(url=url))
		response = requests.post(url, **kwargs)
		return response

	fkwargs = {
		'url': url,
	}
	fkwargs.update(**kwargs)
	response = retry_call(_post,
	                      fkwargs=fkwargs,
						  tries=tries,
						  fail_result=None,
						  wait_random_min=wait_random_min,
						  wait_random_max=wait_random_max,
						  logger=logger)

	if response == None:
		logger.warning('[FAIL] [POST] {url}'.format(url=url))
		return None

	if response.status_code != 200:
		logger.warning('[FAIL] [POST] {url}, for http status: {status_code}'.format(url=url, status_code=response.status_code))
		return None

	logger.info('[SUCCESS] [POST] {url}'.format(url=url))
	# 请求成功后暂停
	logger.debug('[WAIT] {}s'
	             .format(success_wait))
	time.sleep(success_wait)
	return response


def to_file_name(origin_str: str, postfix: str) -> str:
	""" 去掉origin_str中的特殊字符，并添加文件后缀名

	:param origin_str: 需处理的字符串
	:param postfix: 文件后缀(带点号)
	:return: 可用的文件名
	"""
	postfix_len = len(postfix)
	origin_str_len = len(origin_str)

	origin_str = origin_str if origin_str_len + postfix_len <= 255 else origin_str[0 : 255-postfix_len]

	origin_str = origin_str.strip(' ').strip().strip('.'). \
		replace('?', '？'). \
		replace('*', '✳'). \
		replace(':', '：'). \
		replace('"', '“'). \
		replace('<', '《'). \
		replace('>', '》'). \
		replace('\\', '、'). \
		replace('/', '%'). \
		replace('|', '&'). \
		replace('\n', ' '). \
		replace('\t', ' '). \
		replace('\r', ' ')
	return origin_str + postfix


# title -> pdf_file_name
to_pdf_file_name = partial(to_file_name, postfix='.pdf')

# title -> folder_name
to_folder_name = partial(to_file_name, postfix='')


def write(file, path: str, mode: str='w', stream: bool=False, tries: int=2,
		  wait_random_min: int=30, wait_random_max: int=60, logger: Logger=root) -> bool:
	''' 可重试写入

	:param file: 写入内容
	:param path: 写入位置
	:param mode: 写入模式
	:stream: 是否流式写入，True为流式写入，file为response对象;False为普通写入，file为写入数据
	:param tries: 可重时最大次数
	:param wait_random_min: 重试时随机等待最小时间
	:param wait_random_max: 重试时随机等待最大时间
	:param logger:
	:return: bool
	'''
	@retry(tries, fail_result=False, logger=logger,
		   wait_random_min=wait_random_min, wait_random_max=wait_random_max)
	def _retry_write(file, path: str, mode: str='w', stream: bool=False):
		# 文件若已存在，则复制源文件创建临时文件，最后再将临时文件改名、删除原文件
		if os.path.exists(path):
			tempPath = path + '.temp'
			if 'a' in mode:
				shutil.copyfile(path, tempPath)
		else:
			tempPath = path

		encoding = 'utf-8' if 'b' not in mode else None
		logger.debug('[...] [WRITE] {path}'.format(path=path))
		try:
			with open(tempPath, mode, encoding=encoding) as f:
				if stream:
					# 分段下载，下载后立刻写入，不会一直占用内存
					for chunk in file.iter_content(chunk_size=128):
						f.write(chunk)
				else:
					f.write(file)
				f.close()
		except Exception as e:
			# 失败时删除临时文件
			if os.path.exists(tempPath):
				os.remove(tempPath)
			raise e
		else:
			# 成功后将新文件改名，删除原文件
			if tempPath != path:
				deletePath = path + '.delete'
				os.rename(path, deletePath)
				os.rename(tempPath, path)
				os.remove(deletePath)
			return True

	# mode += '+'

	# 检测path上级文件夹是否存在，若不存在则递归创建
	# 将相对路径转换成绝对路径，windows下将路径分隔符都转换成‘\\'
	# windows下路径分隔符为'\\'(也可用'/'),linux下为'/'
	path = os.path.abspath(path)
	folderPath = path.replace('\\', '/').rpartition('/')[0]
	if not os.path.exists(folderPath):
		os.makedirs(folderPath)

	result = _retry_write(file, path, mode=mode, stream=stream)

	if not result:
		logger.warning('[FAIL] [WRITE] {0}'.format(path))
	else:
		logger.info('[SUCCESS] [WRITE] {0}'.format(path))

	return result


# TODO 下载论文
def donwload(url, output_path, logger: Logger=root):
	headers = {
		'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36',
	}
	response = requests_get(url, headers=headers, stream=True, logger=logger)
	if response == None:
		return False

	return write(response, output_path, mode='wb', stream=True, logger=logger)


# TODO 异步写入
@retry(2, fail_result=False, wait_random_min=30, wait_random_max=60)
def async_write(content, path: str, logger: Logger=root) -> bool:
	pass


def get_folders(parent_folder_path: str, logger: Logger=root) -> list:
	''' 返回某个目录下的所有子目录

	:param parent_folder_path:
	:param logger:
	:return:
	'''
	abs_parent_folder_path = os.path.abspath(parent_folder_path)
	folder_paths = []

	# 上级目录不存在
	if not os.path.exists(abs_parent_folder_path):
		logger.warning('[FAIL] get subfolders, {0} is not exists'.format(abs_parent_folder_path))
		return folder_paths

	# 输入不是一个目录
	if not os.path.isdir(abs_parent_folder_path):
		logger.warning('[FAIL] get subfolders, {0} is not a folder'.format(abs_parent_folder_path))
		return folder_paths

	for folder in os.listdir(abs_parent_folder_path):
		folder_path = os.path.join(abs_parent_folder_path, folder)
		if os.path.isdir(folder_path):
			folder_paths.append(folder_path)

	return folder_paths


def updateInfo(info, infos, logPath='', warningPath=''):
	if 'ee' in infos.keys():
		eeTag = etree.Element('ee')
		eeTag.text = infos['ee']
		info.append(eeTag)

	abstractTag = info.find('./abstract')
	pdfURLTag = info.find('./pdfURL')
	referencesTag = info.find('./references')
	citedInPapersTag = info.find('./citedInPapers')

	if not abstractTag is None:
		info.remove(abstractTag)
	if not pdfURLTag is None:
		info.remove(pdfURLTag)
	if not referencesTag is None:
		info.remove(referencesTag)
	if not citedInPapersTag is None:
		info.remove(citedInPapersTag)

	# 创建abstract节点
	abstractTag = etree.Element('abstract')
	# 处理特殊字符，unicode和ASCII不能编码的不能写进xml文档中
	abstractTag.text = re.sub(u"[\x00-\x08\x0b-\x0c\x0e-\x1f]+",u"",infos['abstract'])

	# 创建pdfURL节点
	pdfURLTag = etree.Element('pdfURL')
	pdfURLTag.text = infos['pdfURL']

	# 创建references节点
	referencesTag = etree.Element('references')
	for reference in infos['references']:
		referenceTag = etree.Element('reference')
		# 处理特殊字符
		referenceTag.text = re.sub(u"[\x00-\x08\x0b-\x0c\x0e-\x1f]+",u"",reference)
		referencesTag.append(referenceTag)

	# 创建citedInPapers节点
	citedInPapersTag = etree.Element('citedInPapers')
	for citedInPaper in infos['citedInPapers']:
		citedInPaperTag = etree.Element('citedInpaper')
		# 处理特殊字符
		citedInPaperTag.text = re.sub(u"[\x00-\x08\x0b-\x0c\x0e-\x1f]+",u"",citedInPaper)
		citedInPapersTag.append(citedInPaperTag)

	info.append(pdfURLTag)
	info.append(abstractTag)
	info.append(referencesTag)
	info.append(citedInPapersTag)


def session_get(session: requests.Session, url: str, *, tries: int=3, success_wait: int=0,
                logger: Logger=root, wait_random_min: int=10, wait_random_max: int=30, **kwargs):
	""" 封装session的get请求, 失败可重试请求

	:param session: requests.Session实例
	:param url: 需请求的地址
	:param tries: 最大请求尝试次数
	:param success_wait: 请求成功时暂停多久，默认为0（主要为了应对ACM网站）
	:param logger:
	:param wait_random_min: 重试请求时随机等待的最小时间
	:param wait_random_max: 重试请求时随机等待的最大时间
    :param \*\*kwargs: Optional arguments that ``request`` takes.
	:return: 请求成功返回response对象，失败返回None
	"""

	if url == '' or url == None:
		logger.warning('[FAIL] to excute session_get, the url parameter passed is None')
		return None

	pageURL = (url + '?' + urlencode(kwargs['params'])) if 'params' in kwargs else url

	def _get(url: str, **kwargs):
		nonlocal pageURL
		logger.debug('[...] [SESSION_GET] {0}'.format(pageURL))
		response = session.get(url, **kwargs)
		return response

	fkwargs = {
		'url': url,
	}
	fkwargs.update(kwargs)
	response = retry_call(_get,
	                      fkwargs=fkwargs,
						  tries=tries,
						  fail_result=None,
						  wait_random_min=wait_random_min,
						  wait_random_max=wait_random_max,
						  logger=logger)

	if response == None:
		logger.warning('[FAIL] [SESSION_GET] {url}'.format(url=pageURL))
		return None

	#请求成功，但是状态码不是200
	if response.status_code != 200:
		logger.warning('[FAIL] [SESSION_GET] {url}, for http status: {status_code}'.format(url=pageURL, status_code=response.status_code))
		return None

	# 成功获取到页面，返回response
	logger.info('[SUCCESS] [SESSION_GET] {url}'.format(url=pageURL))
	# 请求成功后暂停
	logger.debug('[WAIT] {}s'
	             .format(success_wait))
	time.sleep(success_wait)
	return response

def session_post(session: requests.Session, url: str, *, tries: int=3, success_wait: int=0, logger: Logger=root,
                  wait_random_min: int=10, wait_random_max: int=30, **kwargs):
	""" 封装session的get请求，失败可重试请求

	:param session: requests.Session实例
	:param url: 需请求的地址
	:param tries: 最大请求尝试次数
	:param success_wait: 成功后暂停时间，默认为0
	:param logger:
	:param wait_random_min: 重试时随机等待最小时间
	:param wait_random_max: 重试时随机等待最大时间
    :param \*\*kwargs: Optional arguments that ``request`` takes.
	:return: 请求成功返回response对象，失败返回None
	"""

	if url == '' or url == None:
		logger.warning('[FAIL] to excute session_post, the url parameter passed is None')
		return None

	def _post(url: str, **kwargs):
		logger.debug('[...] [SESSION_POST] {url}'.format(url=url))
		response = session.post(url, **kwargs)
		return response

	fkwargs = {
		'url': url,
	}
	fkwargs.update(**kwargs)
	response = retry_call(_post,
	                      fkwargs=fkwargs,
						  tries=tries,
						  fail_result=None,
						  wait_random_min=wait_random_min,
						  wait_random_max=wait_random_max,
						  logger=logger)

	if response == None:
		logger.warning('[FAIL] [SESSION_POST] {url}'.format(url=url))
		return None

	if response.status_code != 200:
		logger.warning('[FAIL] [SESSION_POST] {url}, for http status: {status_code}'.format(url=url, status_code=response.status_code))
		return None

	logger.info('[SUCCESS] [SESSION_POST] {url}'.format(url=url))
	# 请求成功后暂停
	logger.debug('[WAIT] {}s'
	             .format(success_wait))
	time.sleep(success_wait)
	return response

def singleton(cls):
	_instance = {}

	def _singleton(*args, **kwargs):
		if cls not in _instance:
			_instance[cls] = cls(*args, **kwargs)
		return _instance[cls]

	return _singleton
