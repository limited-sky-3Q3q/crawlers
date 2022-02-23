# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""parser page from `Aminer`_

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

.. _Aminer:
   https://aminer.cn

"""
__author__ = 'lance'


import json

from .page_parser import PageParser
from ..mylogger import Logger, root
from ..utils import random_user_agent
from ..myrequests import post


class Aminer(PageParser):
	def __init__(self, title: str, response, logger: Logger=root):
		super().__init__(title, response, logger)
		self.document_metadata = self.__get_document_metadata()

	def __get_document_metadata(self):
		if self._element_tree is None:
			self.logger.warning(('Fail get document metadata of {paper},'
			                     'for element tree is None').format(paper=self))
			return None

		xpath = '/html/body/script[1]'

		if len(self._element_tree.xpath(xpath)) <= 0:
			self.logger.warning('[FAIL] get document_metadata of {paper}, maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		try:
			js_code = self._element_tree.xpath(xpath)[0].text
			split_text = 'window.g_initialData ='
			json_data = js_code.split(split_text)[-1].strip(';').strip()

			data = json.loads(json_data)
			self.logger.info('[SUCCESS] get document_metadata of paper <{0}>'.format(self.title))
			return data
		except:
			self.logger.warning('[FAIL] get document_metadata of {paper}'
			                    .format(paper=self), exc_info=True)
			return None

	def get_abstract(self):
		''' get paper abstract

		Returns:
			str: paper abstract if success, None otherwise
		'''
		if not self.document_metadata:
			self.logger.warning('[FAIL] get abstract of {paper}, for no document_metadata'
			                    .format(paper=self))
			return None

		abstract = self.document_metadata.get('paper', {}).get('abstract', '')
		if abstract == '':
			self.logger.warning('[FAIL] get abstract of {paper}, for no abstract'
			                    .format(paper=self))
			return None

		return abstract

	def get_citations(self):
		pass

	def get_references(self):
		pass

	def get_pdf_url(self):
		return None

	def get_author_keywords(self):
		return None

	def get_authors(self):
		if not self.document_metadata:
			self.logger.warning('[FAIL] get authors of {paper}, for no document_metadata'
			                    .format(paper=self))
			return None

		if not ('authorsData' in self.document_metadata.keys() and len(self.document_metadata['authorsData']) > 0):
			self.logger.warning('[FAIL] get authors of {paper}, for no author in document_metadata'
			                    .format(paper=self))
			return None

		try:
			authors = self.document_metadata['authorsData']
			author_infos = []
			for author in authors:
				# FIXME 是否存在多个affiliation的情况
				author_infos.append({
					'name': author['name'].strip(),
					'affiliations': [
						author.get('profile', {}).get('affiliation', '')
							.replace('\r', ' ')
							.replace('\n', '')
							.replace('\t', '')
							.strip(),
					],
					'id': author.get('id', '').strip(),
					'photo_url': author.get('avatar', '').strip(),
				})

			for i in range(len(author_infos)):
				author_infos[i]['publish_affiliation'] = ' and '.join(author_infos[i]['affiliations'])
				author_infos[i]['order'] = i+1
				del author_infos[i]['affiliations']

			self.logger.info('[SUCCESS] get author of {paper}'
			                 .format(paper=self))
			return author_infos
		except:
			self.logger.warning('[FAIL] get authors of {paper}'
			                    .format(paper=self), exc_info=True)
			return None

	def get_keywords(self):
		''' get paper keywords of Aminer

		Returns:
			str: paper keywords if success, None otherwise
		'''
		if not self.document_metadata:
			self.logger.warning('[FAIL] get author keywords of {paper}, for no document_metadata'
			                    .format(paper=self))
			return None

		author_keywords = self.document_metadata.get('paper', {}).get('keywords', '')
		if author_keywords == '':
			self.logger.warning('[FAIL] get author keywords of {paper}, for no author keywords'
			                    .format(paper=self))
			return None

		return author_keywords

	@classmethod
	def search_by_title(cls, title, logger: Logger=root):
		''' 通过title搜索

		:param title:
		:param logger:
		:return:
		'''
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


		url = 'https://apiv2.aminer.cn/magic?a=SEARCH__publication7.SearchPubsCommon___'

		headers = {
			'user-agent': random_user_agent(),
		}
		data = [
			{
				"action": "publication7.SearchPubsCommon",
		        "parameters": {
			        "offset": 0,
			        "size": 20,
			        "searchType": "all",
			        "switches": ["lang_zh"],
                    "query": title,
		        },
		        "schema": {
			        "publication": [
				        "id", "year", "title", "title_zh", "abstract", "abstract_zh", "authors",
		                "authors._id", "authors.name", "keywords", "authors.name_zh", "num_citation",
				        "num_viewed", "num_starred", "num_upvoted", "is_starring", "is_upvoted","is_downvoted",
				        "venue.info.name", "venue.volume", "venue.info.name_zh","venue.info.publisher",
				        "venue.issue", "pages.start", "pages.end", "lang", "pdf", "doi", "urls"
			        ]
		        }
			}
		]

		response = post(url, website='aminer', headers=headers, json=data, logger=logger)

		if response is None:
			logger.warning('[FAIL] search_aminer with title <{title}>, for fail get {url}'
			               .format(title=title, url=url))
			return None

		try:
			json_data = response.json()
			results = json_data['data'][0]['items']
			for result in results:
				if compare_title(title, result['title']):
					logger.info('[SUCCESS_AMINER_SEARCH] find with title <{title}>'
					            .format(title=title))
					return 'https://www.aminer.cn/pub/{id}/{title}' \
						.format(id=result['id'], title=result['title'].replace(' ', '-').lower())

			logger.warning('[FAIL] search_aminer with title <{title}>, for no match result'
			               .format(title=title))
			return None

		except:
			logger.warning('[FAIL] search_aminer with title <{title}>'
			               .format(title=title), exc_info=True)
			return None


if __name__ == '__main__':
	pass