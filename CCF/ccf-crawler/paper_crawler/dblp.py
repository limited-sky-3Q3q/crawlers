# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""module description

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
__author__ = 'lance'


from lxml import etree
import re

from .myrequests import get, post, Session
from .utils import random_user_agent, url_join
from .mylogger import Logger, root


# 年份范围
YEAR_RANGE = (2001, 2020)
# 年份匹配规则，用于journals页面中匹配volume的年份
# FIXME 但是如果volume出现4位数，这样会跟年份匹配冲突
YEAR_PATTERN = re.compile(r'\d{4}')

# 一些比较的会议的venue key
SPECIAL_CONF = {
	'conf/cloud': 'socc',
	'conf/hybrid': 'hscc',
	'conf/ipps': 'ipdps',
	'conf/isw': 'isc',
	'conf/sigsoft': 'fse',
	'conf/kbse': 'ase',
	'conf/lctrts': 'lctes',
	'conf/IEEEscc': 'scc',
	'conf/ssd': 'sstd',
	'conf/icmcs': 'icme',
	'conf/huc': 'UbiComp',
	'conf/acmidc': 'idc',
	'conf/asiaccs': 'conf/ccs/asiaccs'
}


# FIXME 超过10000篇，即f>=10000后，search api无效
def get_all_papers(venue_key: str, logger: Logger=root):
	'''

	:param venue_key: eg: conf/date  journal/tc
	:param logger:
	:return:
	'''
	q = 'stream:streams/{}:'.format(venue_key)
	h = 1000
	format = 'xml'
	f = 0

	try:
		element_tree = search('publ', q, format, h, f, logger=logger)
		hits_element = element_tree.find('.//hits')
		total_num = int(hits_element.get('total'))
		page_num = int(total_num / 1000)

		hit_elements = hits_element.xpath('./hit')
		for hit_element in hit_elements:
			yield hit_element

		for i in range(page_num):
			f += 1000
			element_tree = search('publ', q, format, h, f, logger=logger)
			hit_elements = element_tree.xpath('.//hit')
			for hit_element in hit_elements:

				paper_year = int((hit_element.find('./info/year').text
				                 if hit_element.find('./info/year') is not None else None) or 0)
				if paper_year < 2001:
					print(paper_year)
					break

				yield hit_element
	except:
		logger.warning('[FAIL] get all papers of {}'
		               .format(venue_key), exc_info=True)
		return None

def get_papers_by_year(venue_key: str, logger: Logger=root):
	''' 返回每个年份或者volume的论文集

	Args:
		venue_key: eg. journals/tc/tc69  conf/aaai/aaai2020
		logger:

	Returns:

	'''
	venue_key = venue_key.strip('/')
	q = 'toc:db/{}.bht:'.format(venue_key)
	h = 1000
	format = 'xml'
	f = 0

	try:
		element_tree = search('publ', q, format, h, f, logger=logger)
		hits_element = element_tree.find('.//hits')
		total_num = int(hits_element.get('total'))
		page_num = int(total_num / 1000)

		hit_elements = hits_element.xpath('./hit')
		for hit_element in hit_elements:
			yield hit_element

		for i in range(page_num):
			f += 1000
			element_tree = search('publ', q, format, h, f, logger=logger)
			hit_elements = element_tree.xpath('.//hit')
			for hit_element in hit_elements:
				yield hit_element
	except:
		logger.warning('[FAIL] get all papers of {}'
		               .format(venue_key), exc_info=True)
		return None

def get_conf_papers(conf_key: str, logger: Logger=root):
	''' 获取一个conf的所有论文集

	Args:
		conf_key: eg. conf/date
		logger:

	Returns:

	'''
	conf_key = conf_key.strip('/')
	# 有些会议的每年的key跟conf key不太一样
	if conf_key in SPECIAL_CONF.keys():
		conf_name = SPECIAL_CONF[conf_key]
	else:
		conf_name = conf_key.replace('conf/', '')

	for year in range(YEAR_RANGE[0], YEAR_RANGE[1]+1):
		# 匹配conf/asiacss的情况
		if conf_name.startswith('conf/'):
			venue_key = ('{conf_name}{year}'.format(conf_name=conf_name, year=year))
		else:
			venue_key = ('{conf_key}/{conf_name}{year}'
			             .format(conf_key=conf_key, conf_name=conf_name, year=year))

		# year_num = 0
		for hit_element in get_papers_by_year(venue_key, logger=logger):
			yield (venue_key, hit_element)
			# year_num += 1

		# print('{}: {}'.format(venue_key, year_num))

def get_journals_papers(journals_key: str, logger: Logger=root):
	''' 获取一个期刊的论文集

	Args:
		journals_key: eg. journals/tc
		logger:

	Returns:

	'''
	headers = {
		"user-agent": random_user_agent()
	}
	DBLE_URL = 'https://dblp.uni-trier.de/db/'

	journals_key = journals_key.strip('/')
	journals_url = url_join(DBLE_URL, journals_key)
	year_xpath = '//*[@id="main"]/ul/li'

	response = get(journals_url, headers=headers, website='dblp')
	if response == None:
		logger.warning('[FAIL] get papers of {journals_key}, for can not get {journals_url}'
		               .format(journals_key=journals_key, journals_url=journals_url))
		return None
	try:
		element_tree = etree.HTML(response.text)
		year_tags = element_tree.xpath(year_xpath)
		if len(year_tags) <= 0:
			logger.warning('[FAIL] get papers of {journals_key}, maybe the xapth is wrong'
			               .format(journals_key=journals_key))
			return None

		# 遍历每个年份的行
		for year_tag in year_tags:
			text = ''.join(year_tag.xpath('.//text()'))
			# 可能匹配到多个年份，比如'2004/2005 volume: ...'
			years = re.findall(YEAR_PATTERN, text)
			years.sort()
			year = years[0] if len(years) > 0 else 0

			if year is not None and (int(year) >= YEAR_RANGE[0] and int(year) <= YEAR_RANGE[1]):
				# 一年会有多个volume
				volume_hrefs = year_tag.xpath('.//a/attribute::href')
				if len(volume_hrefs) <= 0:
					logger.warning('[FAIL] get papers of {journals_key}, maybe the xpath is wrong'
					               .format(journals_key=journals_key))
					continue

				for volume_href in volume_hrefs:
					volume_key = volume_href.split('/')[-1].replace('.html', '')
					venue_key = ('{journals_key}/{volume_key}'
					             .format(journals_key=journals_key, volume_key=volume_key))
					# year_num = 0
					for hit_element in get_papers_by_year(venue_key, logger):
						yield (venue_key, hit_element)
						# year_num += 1
					# print('{}: {}'.format(venue_key, year_num))
	except:
		logger.warning('[FAIL] get papers of {journals_key}'
		               .format(journals_key=journals_key), exc_info=True)
		return None

def search(type: str, q: str, format: str='xml', h: int=1000, f: int=0, c: int=0, logger: Logger=root):
	'''

	:param type: ['publ', 'author', 'venue']
	:param q:
	:param format:
	:param h:
	:param f:
	:param c:
	:param logger:
	:return:
	'''
	url = 'https://dblp.org/search/{}/api'.format(type)
	headers = {
		'user-agent': random_user_agent(),
	}
	params = {
		'q': q,
		'format': format,
		'h': h,
		'f': f,
		'c': c
	}

	try:
		response = get(url, website='dblp', headers=headers, params=params)
		if response is None:
			logger.warning('[FAIL] search {q} in dblp'
			               .format(q=q))
			return None

		element_tree = etree.XML(response.content)
		return element_tree
	except:
		logger.warning('[FAIL] search {q} in dblp'
		               .format(q=q), exc_info=True)
		return None


if __name__ == '__main__':
	pass