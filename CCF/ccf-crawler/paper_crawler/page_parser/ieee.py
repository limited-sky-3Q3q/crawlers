# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""parser page from `IEEE`_

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

.. _IEEE:
  https://ieeexplore.ieee.org/

"""

__author__ = 'lance'


from lxml import etree
import json
from copy import deepcopy

from .page_parser import PageParser
from ..mylogger import root, Logger
from ..myrequests import Session, post
from ..utils import random_user_agent


class Ieee(PageParser):

	def __init__(self, title, response, logger: Logger=root):
		super().__init__(title, response, logger)

		#: str: paper article number in IEEE
		self.article_number = self.real_url.strip('/').split('/')[-1].split('?')[0]

		#: dict or None: a dict that includes most of the information of the paper.
		self.__document_metadata = self.__get_document_metadata()

		# self.session = ProxySession('ieee', logger=logger)
		self.session = Session('ieee', logger=logger)

	@property
	def headers(self):
		return {
			'Accept': 'application/json, text/plain, */*',
			'Accept-Encoding': 'gzip, deflate, br',
			'cache-http-response': 'true',
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
			'Host': 'ieeexplore.ieee.org',
			'Referer': 'https://ieeexplore.ieee.org/document/{article_number}'
				.format(article_number=self.article_number)
		}

	def __get_document_metadata(self):
		'''get info (include: abstract, author keywords, authors' info ...)
		in dict format.

		Returns:
			dict, None: Most of the information of the paper if success,
				Non otherwise.

		'''
		# if element tree is None
		if self._element_tree is None:
			self.logger.warning(('Fail get document metadata of {paper},'
			                     'for element tree is None').format(paper=self))
			return None

		# FIXME ieee前端模板有未闭合div, 导致下面xpath不能正常使用
		xpath = ('.//*[@id="LayoutWrapper"]/div[@class="container-fluid"]/'
		         'div[@class="row"]/div[@class="col"]/script[5]')

		# traverse the list of script elements
		# find the script element has text 'document.metadata'.
		script_elements_xpath = '//*[@id="LayoutWrapper"]//script'
		script_element = None
		script_elements = self._element_tree.xpath(script_elements_xpath)
		for element in script_elements:
			if element.text and element.text.find('document.metadata') >= 0:
				script_element = element

		# fail find the script element, maybe the 'script_elements_xpath' is wrong.
		if script_element is None:
			self.logger.warning(('Fail get document metadata of {paper},'
			                     'maybe the xpath is wrong').format(paper=self))
			return None

		# extract the json code included paper info from the text in script element
		js_codes = script_element.text
		spilt_index = js_codes.find('global.document.metadata')
		document_metadata = js_codes[spilt_index:]
		# FIXME 需要更严谨的提取json字符串规则，比如利用‘｛’和‘｝’的位置和个数去匹配
		# 找到第一个等号和josn字符串后的第一个分号，截取中间的json字符串
		document_metadata = document_metadata[document_metadata.find('=')+1 :
		                                      document_metadata.find('"};')+2]

		# json code into dict
		try:
			document_metadata = json.loads(document_metadata)
		except:
			# something error, maybe the json code is wrong.
			self.logger.warning(('Fail get document metadata of {paper}, maybe the'
			                     'json code is wrong').format(paper=self), exc_info=True)
			return None

		return document_metadata

	def __get_metadata(self, info_name):
		'''get paper info from the dict 'document metadata'.

		Args:
			info_name (str): the key of paper info in the dict 'document
				metadata', like 'a/b' means document_metadata['a']['b'].

		Returns:
			paper info if success, None otherwise.

		'''
		names = info_name.split('/')
		info = self.__document_metadata
		try:
			for name in names:
				if name not in info:
					return None
				info = info[name]
		except:
			return None
		return deepcopy(info)

	def get_abstract(self):
		'''get paper abstract

		Returns:
			str, None: paper abstract if success, None otherwise.

		'''
		abstract = self.__get_metadata('abstract')
		# abstract not in document metadata
		if abstract is None:
			self.logger.warning(('Fail get abstract of {paper}, for abstract'
			                     'not in the document metadata').format(paper=self))
		else:
			self.logger.info('Success get abstract of {paper}'.format(paper=self))
		return abstract

	def get_pdf_url(self):
		'''get paper pdf download address

		Returns:
			str, None: pdf download address if success, None otherwise.

		'''
		headers = {
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
		}
		pdf_html_url = ('https://ieeexplore.ieee.org/stamp/stamp.jsp?'
		                'arnumber={number}'.format(number=self.article_number))
		# FIXME proxy get
		# response = requests_get(pdf_html_url, logger=self.logger)
		response = self.session.get(pdf_html_url, headers=headers)

		# fail get page of 'pdf_html_url'
		if response == None:
			self.logger.warning(('Fail get pdf url of {paper},'
			                     'for fail get page: {pdf_html_url}')
			                    .format(paper=self, pdf_html_url=pdf_html_url))
			return None
		try:
			html = etree.HTML(response.content)
			iframe_element = html.xpath('//iframe')[0]
		except:
			self.logger.warning(('Fail get pdf url of {paper}')
			                    .format(paper=self), exc_info=True)
			return None

		pdf_url = iframe_element.get('src')
		self.logger.info('Success get pdf url of {paper}'.format(paper=self))
		return pdf_url

	def get_keywords(self):
		'''get paper keywords (include: IEEE keywords, Author keywords,
		INSPEC: Non-Controlled Indexing, INSPEC: Controlled Indexing).

		Returns:
			:obj: `list` of :obj: 'dict': paper keywords if success, None otherwise.

		'''
		keywords = self.__get_metadata('keywords')
		if keywords is None:
			self.logger.warning('Fail get keywords of {paper}, for keywords'
			                    'not in document metadata'.format(paper=self))
			return None

		self.logger.info('Success get keywords of {paper}'.format(paper=self))
		return keywords

	def get_author_keywords(self):
		'''get paper author keywords

		Returns:
			:obj: `list` of :obj: 'str': paper author keywords if success, None otherwise.

		'''
		keywords = self.get_keywords()
		try:
			for keyword in keywords:
				if ('type' in keyword.keys() and keyword['type'].strip() == 'Author Keywords'):
					self.logger.info('Success get author keywords'
					                 'of {paper}'.format(paper=self))
					return keyword['kwd']

			self.logger.warning('Fail get author keywords of {paper},'
			                    'for no author keywords'.format(paper=self))
			return None
		except:
			self.logger.warning('Fail get author keywords of {paper}'.format(paper=self))
			return None

	def get_authors(self):
		''' get authors' info (include: name, first_name,
			last_name, orcid, id, publish_affiliation, order)

		Returns:
			:obj: `list` of :obj: 'dict': paper authors' info if success, None otherwise.

			Examples:
				{
					[
						"name": "Paolo Montuschi",
				        "first_name": "Paolo",
				        "last_name": "Montuschi",
				        "orcid": "0000-0003-2563-2250",
				        "id": "37085364488",
				        "publish_affiliation": "",
				        "order": 1
				    ],
				    ...
				}
        '''

		# 可从document_metadata中获取作者的基本信息（名字、id、publish_affiliation）
		authors = self.__get_metadata('authors')
		if authors is None:
			self.logger.warning('[FAIL] get authors of {paper}, for authors not in document_metadata'
			               .format(paper=self))
			return None

		# 在document_metadata中获取的affiliation是发表论文时的工作单位
		# 通过author_id去获取到的author具体信息里有currentAffiliation是当前工作单位
		for i in range(len(authors)):
			authors[i]['publish_affiliation'] = authors[i].pop('affiliation') if 'affiliation' in authors[i] else ''
			authors[i]['order'] = i + 1
			if 'firstName' in authors[i]:
				authors[i]['first_name'] = authors[i]['firstName']
				del authors[i]['firstName']
			else:
				authors[i]['first_name'] = ''

			if 'lastName' in authors[i]:
				authors[i]['last_name'] = authors[i]['lastName']
				del authors[i]['lastName']
			else:
				authors[i]['last_name'] = ''

		self.logger.info('[SUCCESS] get authors of {paper}'
		                 .format(paper=self))
		return authors

	# FIXME 返回格式需要确定
	# def get_references(self):
	# 	'''get paper references

	# 	Returns:
	# 		:obj: `list` of :obj: `dict`: paper references if success, None otherwise.

	# 	'''
	# 	has_references = self.__get_metadata('sections/references')
	# 	if has_references == 'false':
	# 		self.logger.warning('Fail get references of {paper},'
	# 		                    'for no references'.format(paper=self))
	# 		return None

	# 	references_url = ('https://ieeexplore.ieee.org/rest/document/{article_number}'
	# 	                  '/references'.format(article_number=self.article_number))
	# 	# response = requests_get(references_url, headers=self.headers)
	# 	# FIXME proxy get
	# 	response = self.session.get(references_url, headers=self.headers)
	# 	if response == None:
	# 		self.logger.warning('Fail get references of {paper}, for fail get {references_url}'
	# 		                    .format(paper=self, references_url=references_url))
	# 		return None

	# 	try:
	# 		json_data = response.json()
	# 	except:
	# 		self.logger.warning('Fail get references of {paper},'
	# 		                    'for json error'.format(paper=self))
	# 		return None
	# 	# print(json.dumps(json_data, indent=4))

	# 	if 'references' not in json_data:
	# 		self.logger.warning('Fail get references of {paper},'
	# 		                    'for no references'.format(paper=self))
	# 		return None

	# 	self.logger.info('Success get references of {paper}'.format(paper=self))
	# 	return json_data['references']

	def get_references(self):
		return None
		
	# FIXME 返回格式需要确定
	# def get_citations(self):
	# 	'''get paper citations (include: paper citations, patent citations)

	# 	Returns:
	# 		dict: paper citations if success, None otherwise.

	# 	'''
	# 	has_citations = self.__get_metadata('sections/citedby')
	# 	if has_citations == 'false':
	# 		self.logger.warning('Fail get citations of {paper},'
	# 		                    'for no citations'.format(paper=self))
	# 		return None

	# 	citations_url = ('https://ieeexplore.ieee.org/rest/document/{article_number}'
	# 	                 '/citations'.format(article_number=self.article_number))
	# 	# response = requests_get(citations_url, headers=self.headers)
	# 	response = self.session.get(citations_url, headers=self.headers)
	# 	if response == None:
	# 		self.logger.warning('Fail get citations of {paper}, for fail get {citations_url}'
	# 		                    .format(paper=self, citations_url=citations_url))
	# 		return None

	# 	try:
	# 		json_data = response.json()
	# 	except:
	# 		self.logger.warning('Fail get citations of {paper},'
	# 		                    'for json error'.format(paper=self))
	# 		return None
	# 	# print(json.dumps(json_data, indent=4))

	# 	citations = {}
	# 	# paper citations
	# 	if 'paperCitations' in json_data and json_data['paperCitations']:
	# 		citations['paper_citations'] = json_data['paperCitations']
	# 	# patent citations
	# 	if 'patentCitations' in json_data and json_data['patentCitations']:
	# 		citations['patent_citations'] = json_data['patentCitations']

	# 	if not citations:
	# 		self.logger.warning('Fail get citations of {paper}, for no'
	# 		                    'paperCitations and patentCitations'.format(paper=self))
	# 		return None

	# 	self.logger.info('Success get citations of {paper}'.format(paper=self))
	# 	return citations

	def get_citations(self):
		return None

	# TODO 作者id搜索可多个作者id，还有其他高级搜索需完善
	# FIXME search term中包含特殊字符，会导致500错误，（eg: Massively Parallel A* Search on a GPU）
	@classmethod
	def __search(cls, search_term, search_type=None, rows_per_page=25, logger: Logger=root):
		'''

		:param type: [title, authors, author_ids, index_terms] (paper标题、作者、作者id、关键词)
		:param search_term: 搜索文本
		:param rows_per_page: 一次搜索结果数
		:param logger:
		:return:
		'''
		search_term = search_term.strip().replace('*', '')
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
			'Content-Type': 'application/json',
			'User-Agent': random_user_agent(),
		}

		jsonData = {
			'highline': True,
			'newsearch': True,
			'queryText': query_text,
			'returnType': 'SEARCH',
			'returnFacets': ['ALL'],
			'rowsPerPage': rows_per_page
		}

		response = post(base_url, website='ieee', headers=headers, json=jsonData, logger=logger)
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

	# 普通搜索
	@classmethod
	def search(cls, search_term, rows_per_page=25, logger: Logger=root):
		''' 普通搜索

		:param search_term: 搜索内容
		:param rows_per_page: 搜索返回结果最大数
		:param logger:
		:return:
		'''
		records = cls.__search(search_term, '', rows_per_page=rows_per_page, logger=logger)
		if records == None:
			return None

		logger.info('[IEEE_SEARCH_SUCCESS] with <{0}>'
		            .format(search_term))
		return records

	@classmethod
	def search_by_index_terms(cls, search_term, rows_per_page=25, logger: Logger=root):
		''' 关键词搜索

		:param search_term: 搜索关键词
		:param rows_per_page: 返回结果最大数
		:param logger:
		:return:
		'''
		records = cls.__search(search_term, 'index_terms', rows_per_page=rows_per_page, logger=logger)
		if records == None:
			return None

		logger.info('[SUCCESS] find with index_terms <{0}>'
		            .format(search_term))
		return records

	# FIXME 没有考虑论文同名的情况，需要再加上论文期刊\会议和出版时间
	@classmethod
	def search_by_title(cls, title, rows_per_page=25, logger: Logger=root):
		''' 通过title搜索

		:param title:
		:param rows_per_page:
		:param logger:
		:return:
		'''
		def compare_title(title, result_title):
			title, result_title = [ x.replace(' ', '')\
			                        .replace('-', '')\
			                        .replace(',', '')\
			                        .replace(':', '')\
			                        .replace('.', '')\
									.replace('*', '')\
			                        .lower()
			                       for x in [title, result_title]
			                    ]
			#FIXME 应该使用相等而不是包含
			# return result_title.find(title) == 0
			return result_title == title

		records = cls.__search(title, 'title', rows_per_page=rows_per_page, logger=logger)
		if records == None:
			return None

		for record in records:
			article_title = record['articleTitle']
			if compare_title(title, article_title):
				logger.info('[IEEE_SEARCH_SUCCESS] find with title <{title}>'
				            .format(title=title))
				return record

		logger.warning('[IEEE_SEARCH_FAIL] find with title <{title}>, for no matching result'
		               .format(title=title))
		return None