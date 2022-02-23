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
import json
import time
from copy import deepcopy
from threading import Lock, Thread

__author__ = 'lance'


from lxml.etree import Element
from queue import Queue
import os
from multiprocessing import Lock

from .db import Client
from .myrequests import Logger, root
from .utils import singleton, url_join, write
from .crawler import PaperCrawler
from .ccf import journals_generator
from .dblp import get_journals_papers, get_conf_papers
from .settings import MONGODB_PORT, MONGODB_HOST, TH_NUM, RECORDS_PATH, USER, PWD


AUTHOR_BASE_URL = {
	'Ieee': 'https://ieeexplore.ieee.org/author/',
	'Acm': 'https://dl.acm.org/profile/',
	'Aminer': 'https://www.aminer.cn/profile/',
	'Elsevier': 'https://www.mendeley.com/authors/',
	'Researchgate': 'https://www.researchgate.net/profile/'
}


@singleton
class CrawlerManager(object):

	def __init__(self, db: Client=None, db_user: str=USER, db_pwd: str=PWD,
	             db_host: str=MONGODB_HOST, db_port: str or int=MONGODB_PORT, logger: Logger=root):
		# db客户端
		self.db = db or Client(user=db_user, pwd=db_pwd, host=db_host, port=db_port)
		self.logger = logger
		self.paper_queue = Queue(100)
		if not os.path.exists(RECORDS_PATH):
			os.makedirs(RECORDS_PATH)

		self.file_lock = Lock()

	def get_unsolved_papers(self):
		''' 获取未被处理的论文

		:return:
		'''
		return self.db.get_unsolved_papers()

	# FIXME 需要改
	# def solve_one_paper(self, venue_key: str, hit_element: Element):
	# 	''' 处理一篇论文
	#
	# 	Args:
	# 		venue_key: 该论文所属的proceedings或volume在dblp中的key
	# 		hit_element:
	#
	# 	Returns:
	#
	# 	'''
	# 	paper_id = hit_element.get('id')
	# 	info_element = hit_element.find('./info')
	# 	venue = info_element.find('./venue').text if info_element.find('./venue') is not None else ''
	# 	paper_type = info_element.find('./type').text if info_element.find('./type') is not None else ''
	#
	# 	key = info_element.find('./key').text
	# 	title = info_element.find('./title').text
	# 	# FIXME 特殊处理
	# 	if title == 'Hardwired Networks on Chip in FPGAs to Unify Functional and Con?guration Interconnects.':
	# 		title = title.replace('?', 'fi').replace('Hardwired', 'rdwired')
	#
	# 	# 不是一篇论文
	# 	if (not (paper_type.lower() in ['journal articles', 'conference and workshop papers'])):
	# 		# logger.error('{title}, {venue}, {paper_type}'
	# 		#              .format(title=title, venue=venue, paper_type=paper_type))
	# 		self.logger.debug('<{title}> is not a paper'
	# 		                  .format(title=title))
	# 		return
	#
	# 	# 在记录文件检索到
	# 	venue_records_path = os.path.join(RECORDS_PATH, venue_key)
	#
	# 	# FIXME 论文已经入库，后面应该会在各个网站都搜一遍，尽量完善各种数据
	# 	exists_paper = self.db.find_one_paper({'key': key})
	# 	if exists_paper:
	# 		self.logger.warning('paper <{key}, {title}> exists already'
	# 		               .format(key=key, title=title))
	#
	# 		# 如果id值不是key的话
	# 		if not exists_paper['_id'] == exists_paper['key']:
	# 			exists_paper_id = exists_paper['_id']
	# 			exists_paper['_id'] = exists_paper['key']
	# 			self.db.add_one_paper({'_id': exists_paper['_id']}, {'$set': exists_paper})
	# 			self.db.remove_one_paper({'_id': exists_paper_id})
	#
	# 		self.file_lock.acquire()
	# 		write(title + '\n', venue_records_path, 'a', logger=self.logger)
	# 		self.file_lock.release()
	# 		return
	#
	# 	# 获取作者在dblp的信息
	# 	author_elements = info_element.xpath('.//author')
	# 	dblp_authors = []
	# 	for i in range(len(author_elements)):
	# 		dblp_authors.append({
	# 			'_id': author_elements[i].get('pid') or '',
	# 			'dblp_name': author_elements[i].text or '',
	# 		})
	#
	# 	# paper pages信息
	# 	if info_element.find('pages') is None:
	# 		self.logger.warning('<{}> has no pages'.format(title))
	# 		pages = ''
	# 	else:
	# 		pages = info_element.find('pages').text
	#
	# 	ees = [ee_element.text for ee_element in info_element.xpath('./ee')]
	# 	ee = ees[0] if len(ees) > 0 else ''
	#
	# 	paper_info = {
	# 		'_id': paper_id,
	# 		'title': title,
	# 		'venue_key': venue_key,
	# 		'venue': venue,
	# 		'year' : info_element.find('./year').text if info_element.find('./year') is not None else 0,
	# 		'type' : paper_type,
	# 		'key' : info_element.find('./key').text if info_element.find('./key') is not None else '',
	# 		'doi' : info_element.find('./doi').text if info_element.find('./doi') is not None else '',
	# 		'volume' : info_element.find('./volume').text if info_element.find('./volume') is not None else '',
	# 		'number' : info_element.find('./number').text if info_element.find('./number') is not None else '',
	# 		'start_page': pages.split('-')[0].strip(),
	# 		'end_page': pages.split('-')[-1].strip(),
	# 		'urls': [],
	# 	}
	#
	# 	paper_crawler = PaperCrawler(paper_info['title'], ee, self.logger)
	# 	paper_info['abstract'] = paper_crawler.get_abstract()
	# 	paper_info['author_keywords'] = paper_crawler.get_author_keywords()
	# 	paper_info['urls'].append(paper_crawler.real_url or '')
	# 	paper_info['references'] = paper_crawler.get_references()
	# 	paper_info['citations'] = paper_crawler.get_citations()
	# 	paper_info['pdf_url'] = paper_crawler.get_pdf_url()
	# 	# 获取aminer关键词
	# 	paper_info['aminer_keywords'] = paper_crawler.get_aminer_keywords()
	# 	paper_info['authors'] = {}
	# 	# 抓取到的作者信息
	# 	authors = paper_crawler.get_authors() or {}
	#
	# 	# 论文中authors字段
	# 	paper_info['authors']['source'] = authors.get('source', '')
	# 	paper_info['authors']['authors'] = deepcopy(dblp_authors)
	#
	# 	author_infos = authors.get('authors', [])
	# 	# print(json.dumps(author_infos, indent=4))
	# 	author_obj_dicts = deepcopy(dblp_authors)
	#
	# 	for i in range(len(author_infos)):
	# 		# 完善论文中作者的信息
	# 		paper_info['authors']['authors'][i]['affiliation'] = author_infos[i]['publish_affiliation']
	# 		paper_info['authors']['authors'][i]['name'] = author_infos[i]['name']
	# 		paper_info['authors']['authors'][i]['order'] = author_infos[i]['order']
	#
	# 		# 完善作者文档
	# 		author_obj_dicts[i]['name'] = author_infos[i]['name']
	# 		author_obj_dicts[i]['last_name'] = author_infos[i].get('last_name', '')
	# 		author_obj_dicts[i]['first_name'] = author_infos[i].get('first_name', '')
	# 		author_obj_dicts[i]['affiliations'] = [author_infos[i]['publish_affiliation']] \
	# 			if author_infos[i].get('publish_affiliation') else []
	# 		author_obj_dicts[i]['orcid'] = author_infos[i].get('orcid', '') or ''
	# 		author_obj_dicts[i]['email'] = author_infos[i].get('email', '') or ''
	# 		author_obj_dicts[i]['photo_url'] = author_infos[i].get('photo-url', '') or ''
	# 		# author_obj_dicts[i]['aliases'] = author_infos[i].get('aliases', []) or []
	#
	# 		# 作者链接地址
	# 		author_obj_dicts[i]['urls'] = []
	# 		if (AUTHOR_BASE_URL.get(paper_crawler.page_parser_name or '', '') and
	# 				author_obj_dicts[i].get('id', '')):
	# 			author_obj_dicts[i]['urls'].append(url_join(AUTHOR_BASE_URL[paper_crawler.page_parser_name],
	# 			                                            author_obj_dicts[i]['id']))
	#
	# 	# print(json.dumps(paper_info, indent=4))
	# 	# print(json.dumps(author_obj_dicts, indent=4))
	# 	# return paper_info, author_obj_dicts
	#
	# 	# paper入库
	# 	self.db.add_one_paper({'_id': paper_info['_id']}, {'$set': paper_info})
	# 	# FIXME 没有考虑写入数据库失败的情况
	# 	self.file_lock.acquire()
	# 	write(title + '\n', venue_records_path, 'a', logger=self.logger)
	# 	self.file_lock.release()
	# 	self.logger.info('save {venue_key}, {title}'
	# 	                 .format(venue_key=venue_key, title=title))
	# 	for author_obj_dict in author_obj_dicts:
	# 		# 作者已经入库了，就只更新affiliation、urls
	# 		author = self.db.find_one_author({'_id': author_obj_dict['_id']})
	# 		if author:
	# 			update_dict = {}
	# 			if 'affiliations' not in author.keys():
	# 				author['affiliations'] = []
	# 			author['affiliations'].extend(author_obj_dict.get('affiliations', []))
	# 			update_dict['affiliations'] = list(set(author['affiliations']))
	#
	# 			if 'urls' not in author.keys():
	# 				author['urls'] = []
	# 			author['urls'].extend(author_obj_dict.get('urls', []))
	# 			update_dict['urls'] = list(set(author['urls']))
	#
	# 			self.db.update_one_author({'_id': author_obj_dict['_id']}, {'$set': update_dict})
	# 		else:
	# 			self.db.add_one_author({'_id': author_obj_dict['_id']}, {'$set': author_obj_dict})

	def solve_one_paper(self, unsolved_paper: dict):
		''' 处理一篇还未被处理的论文

		Args:
			unsolved_paper:

		Returns:

		'''
		ee = unsolved_paper.get('ees', [''])[0]
		paper_crawler = PaperCrawler(unsolved_paper['title'], ee, self.logger)
		if 'urls' not in unsolved_paper.keys():
			unsolved_paper['urls'] = []

		unsolved_paper['abstract'] = paper_crawler.get_abstract()
		unsolved_paper['author_keywords'] = paper_crawler.get_author_keywords()
		unsolved_paper['urls'].append(paper_crawler.real_url or '')
		unsolved_paper['references'] = paper_crawler.get_references()
		unsolved_paper['citations'] = paper_crawler.get_citations()
		unsolved_paper['pdf_url'] = paper_crawler.get_pdf_url()
		# 获取aminer关键词
		unsolved_paper['aminer_keywords'] = paper_crawler.get_aminer_keywords()
		unsolved_paper['authors'] = {}
		# 抓取到的作者信息
		authors = paper_crawler.get_authors() or {}

		# 论文中authors字段
		unsolved_paper['authors']['source'] = authors.get('source', '')
		unsolved_paper['authors']['authors'] = deepcopy(unsolved_paper['dblp_authors'])

		author_infos = authors.get('authors', [])
		# print(json.dumps(author_infos, indent=4))
		author_obj_dicts = deepcopy(unsolved_paper['dblp_authors'])

		for i in range(len(author_infos)):
			# 完善论文中作者的信息
			unsolved_paper['authors']['authors'][i]['affiliation'] = author_infos[i]['publish_affiliation']
			unsolved_paper['authors']['authors'][i]['name'] = author_infos[i]['name']
			unsolved_paper['authors']['authors'][i]['order'] = author_infos[i]['order']

			# 完善作者文档
			author_obj_dicts[i]['name'] = author_infos[i]['name']
			author_obj_dicts[i]['last_name'] = author_infos[i].get('last_name', '')
			author_obj_dicts[i]['first_name'] = author_infos[i].get('first_name', '')
			author_obj_dicts[i]['affiliations'] = [author_infos[i]['publish_affiliation']] \
				if author_infos[i].get('publish_affiliation') else []
			author_obj_dicts[i]['orcid'] = author_infos[i].get('orcid', '') or ''
			author_obj_dicts[i]['email'] = author_infos[i].get('email', '') or ''
			author_obj_dicts[i]['photo_url'] = author_infos[i].get('photo-url', '') or ''
			# author_obj_dicts[i]['aliases'] = author_infos[i].get('aliases', []) or []

			# 作者链接地址
			author_obj_dicts[i]['urls'] = []
			if (AUTHOR_BASE_URL.get(paper_crawler.page_parser_name or '', '') and
					author_obj_dicts[i].get('id', '')):
				author_obj_dicts[i]['urls'].append(url_join(AUTHOR_BASE_URL[paper_crawler.page_parser_name],
				                                            author_obj_dicts[i]['id']))

		# print(json.dumps(paper_info, indent=4))
		# print(json.dumps(author_obj_dicts, indent=4))
		# return paper_info, author_obj_dicts

		unsolved_paper['solved'] = True
		# paper入库
		self.db.add_one_paper({'_id': unsolved_paper['_id']}, {'$set': unsolved_paper})
		self.logger.info('save {id}, {title}'
		                 .format(id=unsolved_paper['_id'], title=unsolved_paper['title']))
		# print(json.dumps(unsolved_paper, indent=4))

		for author_obj_dict in author_obj_dicts:
			# 作者已经入库了，就只更新affiliation、urls
			author = self.db.find_one_author({'_id': author_obj_dict['_id']})
			if author:
				update_dict = {}
				if 'affiliations' not in author.keys():
					author['affiliations'] = []
				author['affiliations'].extend(author_obj_dict.get('affiliations', []))
				update_dict['affiliations'] = list(set(author['affiliations']))

				if 'urls' not in author.keys():
					author['urls'] = []
				author['urls'].extend(author_obj_dict.get('urls', []))
				update_dict['urls'] = list(set(author['urls']))

				self.db.update_one_author({'_id': author_obj_dict['_id']}, {'$set': update_dict})
				# print(json.dumps(update_dict, indent=4))
			else:
				self.db.add_one_author({'_id': author_obj_dict['_id']}, {'$set': author_obj_dict})
				# print(json.dumps(author_obj_dict, indent=4))

	# FIXME 改
	def solve_papers(self):
		''' 处理还未被处理的论文

		:return:
		'''
		def __do_task(queue: Queue):
			while True:
				if queue.empty():
					time.sleep(1)
					continue

				unsolved_paper= queue.get()
				try:
					self.solve_one_paper(unsolved_paper)
				except:
					self.logger.error('something error', exc_info=True)

		def __put_papers(queue: Queue):
			with self.get_unsolved_papers() as unsolved_papers:
				for unsolved_paper in unsolved_papers:
					queue.put(unsolved_paper)

			queue.join()

		put_th = Thread(target=__put_papers, args=(self.paper_queue,), name='put_th')
		put_th.start()

		ths = []
		for i in range(TH_NUM):
			th = Thread(target=__do_task, args=(self.paper_queue,))
			th.start()
			ths.append(th)

		put_th.join()
		for th in ths:
			th.join()

	# def get_dblp_papers(self):
	# 	for journal in journals_generator():
	# 		papers = []
	# 		if journal.startswith('journals/'):
	# 			papers = get_journals_papers(journal)
	# 		elif journal.startswith('conf/'):
	# 			papers = get_conf_papers(journal)
	# 		else:
	# 			self.logger.warning('incorrect journal\\conf name {}'
	# 			                    .format(journal))
	#
	# 		solved_records = {}
	# 		for paper in papers:
	# 			if solved_records.get(paper[0], None) is None:
	# 				solved_records[paper[0]] = []
	# 				records_path = os.path.join(RECORDS_PATH, paper[0])
	# 				if os.path.exists(records_path):
	# 					with open(records_path, 'r', encoding='utf-8') as f:
	# 						for line in f:
	# 							solved_records[paper[0]].append(line.strip())
	#
	# 			title = paper[1].find('./info/title').text if paper[1].find('./info/title') is not None else ''
	# 			if title in solved_records[paper[0]]:
	# 				self.logger.warning('paper <{title}> exists already'
	# 				                    .format(title=title))
	# 				continue
	#
	# 			yield (paper[0], paper[1])
	#
	# 		del solved_records

	def get_dblp_papers(self):
		''' 从dblp上面获取整个期刊\会议的论文

		:return:
		'''
		for journal in journals_generator():
			papers = []
			if journal.startswith('journals/'):
				papers = get_journals_papers(journal)
			elif journal.startswith('conf/'):
				papers = get_conf_papers(journal)
			else:
				self.logger.warning('incorrect journal\\conf name {}'
				                    .format(journal))

			solved_records = {}
			for paper in papers:
				if solved_records.get(paper[0], None) is None:
					solved_records[paper[0]] = []
					records_path = os.path.join(RECORDS_PATH, paper[0])
					if os.path.exists(records_path):
						with open(records_path, 'r', encoding='utf-8') as f:
							for line in f:
								solved_records[paper[0]].append(line.strip())

				title = paper[1].find('./info/title').text if paper[1].find('./info/title') is not None else ''
				if title in solved_records[paper[0]]:
					self.logger.warning('paper <{title}> exists already'
					                    .format(title=title))
					continue

				yield (paper[0], paper[1])

			del solved_records

	def save_one_dblp_paper(self, venue_key: str, hit_element: Element):
		''' 从dblp上面获取一篇论文并入库

		Args:
			venue_key: 该论文所属的proceedings或volume在dblp中的key
			hit_element:

		Returns:

		'''
		info_element = hit_element.find('./info')
		venue = info_element.find('./venue').text if info_element.find('./venue') is not None else ''
		paper_type = info_element.find('./type').text if info_element.find('./type') is not None else ''

		key = info_element.find('./key').text
		title = info_element.find('./title').text
		# FIXME 特殊处理
		if title == 'Hardwired Networks on Chip in FPGAs to Unify Functional and Con?guration Interconnects.':
			title = title.replace('?', 'fi').replace('Hardwired', 'rdwired')

		# 不是一篇论文
		if (not (paper_type.lower() in ['journal articles', 'conference and workshop papers'])):
			# logger.error('{title}, {venue}, {paper_type}'
			#              .format(title=title, venue=venue, paper_type=paper_type))
			self.logger.debug('<{title}> is not a paper'
			                  .format(title=title))
			return

		# 在记录文件检索到
		venue_records_path = os.path.join(RECORDS_PATH, venue_key)

		# 论文已经入库了
		exists_paper = self.db.find_one_paper({'_id': key})
		if exists_paper:
			self.logger.warning('paper <id={key}, title={title}> exists already'
			               .format(key=key, title=title))

			self.file_lock.acquire()
			write(title + '\n', venue_records_path, 'a', logger=self.logger)
			self.file_lock.release()
			return

		# 获取作者在dblp的信息
		author_elements = info_element.xpath('.//author')
		dblp_authors = []
		for i in range(len(author_elements)):
			dblp_authors.append({
				'_id': author_elements[i].get('pid') or '',
				'dblp_name': author_elements[i].text or '',
			})

		# paper pages信息
		if info_element.find('pages') is None:
			self.logger.warning('<{}> has no pages'.format(title))
			pages = ''
		else:
			pages = info_element.find('pages').text

		ees = [ee_element.text for ee_element in info_element.xpath('./ee')]

		paper_info = {
			'_id': key,
			'title': title,
			'venue_key': venue_key,
			'venue': venue,
			'type' : paper_type,
			'year' : info_element.find('./year').text if info_element.find('./year') is not None else 0,
			'doi' : info_element.find('./doi').text if info_element.find('./doi') is not None else '',
			'volume' : info_element.find('./volume').text if info_element.find('./volume') is not None else '',
			'number' : info_element.find('./number').text if info_element.find('./number') is not None else '',
			'start_page': pages.split('-')[0].strip(),
			'end_page': pages.split('-')[-1].strip(),
			'ees': ees,
			'dblp_authors': dblp_authors
		}

		# paper入库
		self.db.add_one_paper({'_id': paper_info['_id']}, {'$set': paper_info})
		# FIXME 没有考虑写入数据库失败的情况
		self.file_lock.acquire()
		write(title + '\n', venue_records_path, 'a', logger=self.logger)
		self.file_lock.release()
		self.logger.info('save <dblp paper, id={venue_key}, title={title}>'
		                 .format(venue_key=venue_key, title=title))

	def save_dblp_papers(self):
		''' 从dblp上面获取论文

		:return:
		'''
		def __do_task(queue: Queue):
			while True:
				if queue.empty():
					time.sleep(1)
					continue

				venue_key, hit_element = queue.get()
				try:
					self.save_one_dblp_paper(venue_key, hit_element)
				except:
					self.logger.error('something error', exc_info=True)

		def __put_papers(queue: Queue):
			dblp_papers = self.get_dblp_papers()
			for paper in dblp_papers:
				queue.put(paper)

			queue.join()

		put_th = Thread(target=__put_papers, args=(self.paper_queue,), name='put_th')
		put_th.start()

		ths = []
		for i in range(TH_NUM):
			th = Thread(target=__do_task, args=(self.paper_queue,))
			th.start()
			ths.append(th)

		put_th.join()
		for th in ths:
			th.join()


if __name__ == '__main__':
	pass