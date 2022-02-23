# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""parser page from `Researchgate`_

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

.. _Researchgate:
   https://www.researchgate.net

"""

__author__ = 'lance'


from lxml import etree
import json

from .page_parser import PageParser
from ..utils import random_user_agent, url_join
from ..mylogger import Logger, root
from ..myrequests import get


# FIXME 需要逆向js获取cookie，否则会429
class Researchgate(PageParser):
	def __init__(self, title: str, response, logger: Logger=root):
		super().__init__(title, response, logger)
		self.document_metadata = self.__get_document_metadata()

	def __get_document_metadata(self):
		if self._element_tree is None:
			self.logger.warning(('Fail get document metadata of {paper},'
			                     'for element tree is None').format(paper=self))
			return None

		xpath = '//script[@type="application/ld+json"]'

		if len(self._element_tree.xpath(xpath)) <= 0:
			self.logger.warning('[FAIL] get document_metadata of {paper}, maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		try:
			json_data = self._element_tree.xpath(xpath)[0].text
			data = json.loads(json_data)
			self.logger.info('[SUCCESS] get document_metadata of paper <{0}>'.format(self.title))
			return data
		except:
			self.logger.warning('[FAIL] get document_metadata of {paper}'
			                    .format(paper=self), exc_info=True)
			return None

	def get_abstract(self):
		if self._element_tree is None:
			self.logger.warning(('[FAIL] get abstract of {paper},'
			                     'for element tree is None').format(paper=self))
			return None

		xpath = '//div[@itemprop="description"]/text()'

		abstract = self._element_tree.xpath(xpath)
		if len(abstract) <= 0:
			self.logger.warning('[FAIL] get abstract of {paper}, for no abstract,'
			                    ' or maybe the xpath is wrong'.format(paper=self))
			return None

		self.logger.info('[SUCCESS] get abstract of {paper}'
		                 .format(paper=self))
		return abstract[0].strip()

	# TODO
	def get_citations(self):
		return None

	def get_pdf_url(self):
		return None

	# TODO
	def get_references(self):
		return None

	def get_author_keywords(self):
		return None

	def get_authors(self):
		if not self.document_metadata:
			self.logger.warning('[FAIL] get authors of {paper}, for no document_metadata'
			                    .format(paper=self))
			return None

		if not ('author' in self.document_metadata.keys() and len(self.document_metadata['author']) > 0):
			self.logger.warning('[FAIL] get authors of {paper}, for no author in document_metadata'
			                    .format(paper=self))
			return None

		try:
			authors = self.document_metadata['author']
			author_infos = []
			author_order = 1
			for author in authors:
				if author['@type'] == 'Person':
					author_infos.append({
						'order': author_order,
						'name': author['name'].strip(),
						'photo_url': author.get('image', '').strip(),
						'id': author['url'].split('/')[-1].strip() \
							if author['url'].find('profile') >= 0 else '',
						'publish_affiliation': author['memberOf']['name'] \
							if author.get('memberOf', {}).get('@type', '') == 'Organization' else '',
					})
					author_order += 1

			self.logger.info('[SUCCESS] get author of <{paper}>'
			                 .format(paper=self))
			return author_infos
		except:
			self.logger.warning('[FAIL] get authors of {paper}'
			                    .format(paper=self), exc_info=True)
			return None

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


		url = 'https://www.researchgate.net/search'
		headers = {
			'user-agent': random_user_agent(),
			'upgrade-insecure-requests': '1',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'sec-fetch-user': '?1',
			'sec-fetch-site': 'none',
			'sec-fetch-mode': 'navigate',
			'cache-control': 'max-age=0',
		}
		params = {
			'q': title,
		}
		response = get(url, website='researchgate', params=params, headers=headers, logger=logger)

		if response is None:
			logger.warning('[FAIL] search_searchgate with title <{title}>, for fail get {url}'
			               .format(title=title, url=url))
			return None

		element_tree = etree.HTML(response.text)
		script_xpath = './/script[contains(text(), "{title}")]'.format(title=title)


		try:
			js_code = element_tree.xpath(script_xpath)[0].text if len(element_tree.xpath(script_xpath)) > 0 else ''
			if not js_code:
				logger.warning('[FAIL] search_searchgate with title <{title}>, fail get js_code, maybe the xpath is wrong'
				               .format(title=title))
				return None

			# s_split_index = js_code.find('"data":')
			s_split_index = js_code.find('RGCommons.react.mountWidgetTree(')

			js_code = js_code[s_split_index + len('RGCommons.react.mountWidgetTree(') : ]
			# e_split_index = js_code.find(',"templateName"')
			e_split_index = js_code.find(');')
			js_code = js_code[ : e_split_index]
			# print(js_code)

			data = json.loads(js_code)
			results = data['data']['searchItemsList']['data']['items']

			for result in results:
				result_data = result['data']['publication']
				result_title = result_data['title']
				if compare_title(title, result_title):
					logger.info('[SUCCESS_SEARCHGATE_SEARCH] find with title <{title}>'
					            .format(title=title))
					return url_join('https://www.researchgate.net/', result_data['url'].split('?')[0])

			logger.warning('[FAIL] search_searchgate with title <{title}>, for no match result'
			               .format(title=title))
			return None

		except:
			logger.warning('[FAIL] search_searchgate with title <{title}>'
			               .format(title=title), exc_info=True)
			return None


if __name__ == '__main__':
	pass