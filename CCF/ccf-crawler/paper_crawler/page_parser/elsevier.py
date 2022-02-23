# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""parser page from `Elsevier`_

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

.. _Elsevier:
   https://www.sciencedirect.com

"""

__author__ = 'lance'


import json
from lxml import etree

from .page_parser import PageParser
from ..mylogger import Logger, root
from ..utils import random_user_agent
from ..myrequests import Session, get
from ..utils import url_join


class Elsevier(PageParser):
	def __init__(self, title: str, response, logger: Logger=root):
		super().__init__(title, response, logger)

		#: str: paper id in Elsevier
		self.article_number = self.real_url.split('/')[-1].split('?')[0]

		#: dict or None: a dict that includes most of the information of the paper.
		self.__document_metadata = self.__get_document_metadata()

		self.session = Session('sciencedirect', logger=logger)

	def __get_document_metadata(self):
		xpath = '//script[@type="application/json"]/text()'
		json_str = self._element_tree.xpath(xpath)
		if len(json_str) <= 0:
			self.logger.warning('[FAIL] get document_metadata of {paper}, maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		try:
			document_metadata = json.loads(json_str[0])
		except:
			self.logger.warning('[FAIL] get document_metadata of {paper}'
			                    .format(paper=self), exc_info=True)
			return None

		return document_metadata

	def get_abstract(self):
		if self.__document_metadata is None:
			self.logger.warning('[FAIL] get abstract of {paper}, for no document_metadata'
			                    .format(paper=self))
			return None

		if 'abstracts' not in self.__document_metadata.keys():
			self.logger.warning('[FAIL] get abstract of {paper}, for no authors in document_metadata'
			                    .format(paper=self))
			return None

		abstracts = []
		contents = self.__document_metadata['abstracts'].get('content', [])
		for content in contents:
			sub_contents = content.get('$$', [])
			for sub_content in sub_contents:
				if sub_content.get('_', '') == 'Abstract':
					for sub_content in sub_contents:
						if sub_content.get('#name', '') == 'abstract-sec':
							abstracts = sub_content.get('$$', [])
							break
					break
			if len(abstracts) > 0:
				break

		if len(abstracts) <= 0:
			self.logger.warn('[FAIL] get abstract of {paper}, for no abstract,'
			                 'or maybe parsering the json data is wrong'.format(paper=self))
			return None

		abstract_texts = []
		for abstract in abstracts:
			if abstract.get('#name', 'simple-para'):
				abstract_texts.append(abstract.get('_', '').strip())

		abstract = ' '.join(abstract_texts)
		self.logger.info('[SUCCESS] get abstract of {paper}'
		                 .format(paper=self))
		return abstract

	def get_pdf_url(self):
		return None

	# TODO 游客无法获取，个别免费论文可以获取
	def get_references(self):
		return None

	# TODO 参数破解太麻烦，一个字懒
	def get_citations(self):
		return None

	def __get_author_ids(self, authors_num):
		headers = {
			'user-agent': random_user_agent(),
		}
		INDEXTOORDER = {
			'1': '1st',
			'2': '2nd',
			'3': '3rd',
		}
		url = 'https://www.sciencedirect.com/sdfe/arp/pii/' + self.article_number + '/author/{author_index}/articles'
		author_ids = []

		for i in range(1, authors_num+1):
			response = self.session.get(url.format(author_index=i), headers=headers)
			try:
				json_data = response.json()
				author_ids.append(json_data['scopusAuthorId'])
			except:
				self.logger.warning('[FAIL] get {author_index} author\'s id of {paper}'
				                    .format(paper=self,
				                            author_index=INDEXTOORDER[str(i)] if i in range(1, 4) else str(i) + 'th'),
				                    exc_info=True)
				author_ids.append('')
				continue

		return author_ids

	def get_authors(self):
		''' get paper author's info
		
		Returns:
			:obj: 'list' of :obj: 'dict': paper authors' info if success, None otherwise
		'''
		if self.__document_metadata is None:
			self.logger.warning('[FAIL] get authors of {paper}, for no document_metadata'
			                    .format(paper=self))
			return None

		if 'authors' not in self.__document_metadata.keys():
			self.logger.warning('[FAIL] get authors of {paper}, for no authors in document_metadata'
			                    .format(paper=self))
			return None

		# FIXME 字典键可能不存在
		# get affiliations
		affiliations = self.__document_metadata['authors']['affiliations']

		metadatas = self.__document_metadata['authors']['content'][0]['$$']
		authors = []
		for metadata in metadatas:
			if metadata['#name'] == 'author':
				author = {}
				author_data = metadata['$$']
				author['affiliations'] = []
				for data in author_data:
					if data['#name'] == 'given-name':
						author['first_name'] = data['_'].strip()
					if data['#name'] == 'surname':
						author['last_name'] = data['_'].strip()
					# 这里只获取affiliation, 联系方式（电话）暂不获取
					if data['#name'] == 'cross-ref':
						ref_id = data['$']['refid'].strip()
						if ref_id in affiliations.keys():
							aff_text = ''
							for o in affiliations[ref_id]['$$']:
								if o['#name'] == 'textfn':
									aff_text = o['_'].strip()
							author['affiliations'].append(aff_text)

					if data['#name'] == 'e-address':
						author['email'] = data['_'].strip()
				authors.append(author)

		author_ids = self.__get_author_ids(len(authors))
		author_order = 1
		for author in authors:
			author['id'] = author_ids[authors.index(author)].strip()
			author['name'] = author['first_name'] + ' ' + author['last_name']
			author['publish_affiliation'] = ' and '.join(author['affiliations'])
			del author['affiliations']
			author['order'] = author_order
			author_order += 1

		self.logger.info('[SUCCESS] get authors of {paper}'
		                 .format(paper=self))
		return authors

	def get_author_keywords(self):
		''' get paper author keywords

		Returns:
			list: paper author keywords if success, None otherwise
		'''
		if self.__document_metadata is None:
			self.logger.warning('[FAIL] get author-keywords of {paper}, for no document_metadata'
			                    .format(paper=self))
			return None

		if 'combinedContentItems' not in self.__document_metadata.keys() or self.__document_metadata['combinedContentItems'] == {}:
			self.logger.warning('[FAIL] get author-keywords of {paper}, for no author-keywords'
			                    .format(paper=self))
			return None

		author_keywords = []
		# 提取author-keywords
		try:
			for content in self.__document_metadata['combinedContentItems']['content']:
				if content['#name'] == 'keywords':
					keyword_contents = content['$$']
					for keyword_content in keyword_contents:
						if keyword_content['#name'] == 'keywords':
							keywords = keyword_content['$$']
							for keyword in keywords:
								if keyword['#name'] == 'keyword':
									for o in keyword['$$']:
										if o['#name'] == 'text':
											author_keywords.append(o['_'])
											break
							break
					break
		except:
			self.logger.warning('[FAIL] get author-keywords of {paper}, for'
			                    .format(paper=self), exc_info=True)
			return None

		# 可能是解析代码出错
		if len(author_keywords) <= 0:
			self.logger.warning('[FAIL] get author-keywords of {paper}, for no author-keywords, or maybe the parser code is wrong'
			                    .format(paper=self))
			return None

		self.logger.info('[SUCCESS] get author-keywords of {paper}'
		                 .format(paper=self))
		return author_keywords

	@classmethod
	def search_by_title(self, title, logger: Logger=root):
		def compare_title(title, result_title):
			title, result_title = [ x.replace(' ', '')\
			                        .replace('-', '')\
			                        .replace(',', '')\
			                        .replace(':', '')\
			                        .replace('.', '')\
			                        .lower()
			                       for x in [title, result_title]
			                    ]
			#FIXME 应该使用相等而不是包含
			# return result_title.find(title) == 0
			return result_title == title

		# 将title文本从带有<em>等标签的字符串中分离出来
		def separate_title(title):
			title = '<html>' + title + '</html>'
			# html可以包容<ce:inf loc=post>这样的标签，但是xml不能
			element = etree.HTML(title)
			title_texts = element.xpath('.//text()')
			return ''.join(title_texts)

		headers = {
			'user-agent': random_user_agent(),
		}
		url = 'https://www.sciencedirect.com/search/api'
		title = title.strip()
		params = {
			'title': title,
		}

		response = get(url, website='sciencedirect', headers=headers, params=params, logger=logger)
		if response is None:
			logger.warning('[SCIENCEDIRECT_SEARCH_FAIL] find with title <{title}>, for network error'
			               .format(title=title))
			return None

		try:
			search_results = response.json()['searchResults']
			if len(search_results) <= 0:
				logger.warning('[SCIENCEDIRECT_SEARCH_FAIL] find with title <{title}>, for no results'
				               .format(title=title))
				return None

			for search_result in search_results:
				result_title = separate_title(search_result['title'])
				if compare_title(title, result_title):
					result_url = url_join('https://www.sciencedirect.com/', search_result['link'])
					logger.info('[SCIENCEDIRECT_SEARCH_SUCCESS] find with title <{title}>'
					            .format(title=title))
					return result_url
		except:
			logger.warning('[SCIENCEDIRECT_SEARCH_FAIL] find with title <{title}>'
			               .format(title=title), exc_info=True)
			return None

		logger.warning('[SCIENCEDIRECT_SEARCH_FAIL] find with title <{title}>, for no match result'
		               .format(title=title))
		return None


if __name__ == '__main__':
	pass