import re
import random
import requests
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.parse import urlunparse
from posixpath import normpath
from binascii import b2a_hex

from .ocr import ocr
from .error import UnknowImgTypeError


proxy_format_pattern = re.compile(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}:\d+')
def check_proxy_format(proxy):
	return re.match(proxy_format_pattern, proxy) is not None

def random_user_agent():
	user_agents = [
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

# 单例模式
def singleton(cls):
	_instance = {}

	def _singleton(*args, **kwargs):
		if cls not in _instance:
			_instance[cls] = cls(*args, **kwargs)
		return _instance[cls]

	return _singleton

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

def image_to_string(img_path: str):
	try:
		return ocr(img_path)
	except Exception as e:
		raise e
	
def get_img_type(stream_first4bytes):
	'''

	:param stream_first4bytes: 图片字节流的前四位
	:return: 返回图片类型
	'''

	bytes_hex = b2a_hex(stream_first4bytes)
	if bytes_hex.startswith(b'ffd8'):
		file_type = '.jpeg'
	elif bytes_hex == b'89504e47':
		file_type = '.png'
	elif bytes_hex == b'47494638':
		file_type = '.gif'
	elif bytes_hex.startswith(b'424d'):
		file_type = '.bmp'
	else:
		raise UnknowImgTypeError

	return file_type