# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""parser page from `AAAI`_

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

.. _AAAI:
   https://aaai.org

"""
__author__ = 'lance'


from lxml import etree

from .page_parser import PageParser
from ..myrequests import Logger, root
from ..utils import random_user_agent, url_join
from ..myrequests import get


class Aaai(PageParser):
	def __init__(self, title: str, response, logger: Logger=root):
		super().__init__(title, response, logger)

		# ojs \ ocs
		self.type = self.real_url.replace('https://www.aaai.org/', '').replace('https://aaai.org/', '').split('/')[0]
		# 例如https://www.aaai.org/ocs/index.php/ICAPS/ICAPS15/paper/view/10602 需要将view换成viewPaper才能获取到真正页面
		if self.type == 'ocs':
			if 'viewPaper' not in self.real_url and 'view' in self.real_url:
				self.real_url = self.real_url.replace('view', 'viewPaper')
				headers = {
					'user-agent': random_user_agent(),
				}
				# FIXME requests_get_with_proxy
				response = get(self.real_url, website='aaai', headers=headers)
		try:
			self._element_tree = etree.HTML(response.content)
			self.real_url = response.url
		except:
			self._element_tree = None

	def get_abstract(self):
		''' get paper abstract

		Returns:
			str: paper abstract if success, None otherwise
		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get abstract of {paper}, for no _element_tree'
			                    .format(paper=self))
			return None

		abstract_xpath = '//meta[@name="DC.Description"]/attribute::content'

		abstract = self._element_tree.xpath(abstract_xpath)
		if len(abstract) <= 0:
			self.logger.warning('[FAIL] get abstract of {paper}, for no abstract, or maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		self.logger.info('[SUCCESS] get abstract of {paper}'
		                 .format(paper=self))
		return abstract[0]

	def get_citations(self):
		return None

	def get_references(self):
		return None

	def get_pdf_url(self):
		if self._element_tree is None:
			self.logger.warning('[FAIL] get pdf url of {paper}, for no _element_tree'
			                    .format(paper=self))
			return None

		pdf_url_xpath = ''
		if self.type == 'ojs':
			pdf_url_xpath = '//a[@class="obj_galley_link pdf"]/attribute::href'
		elif self.type == 'ocs':
			pdf_url_xpath = '//a[text()="PDF"]/attribute::href'

		pdf_url = self._element_tree.xpath(pdf_url_xpath)
		if len(pdf_url) <= 0:
			self.logger.warning('[FAIL] get pdf url of {paper}, for no pdf url, '
			                    'or maybe the xpath is wrong'.format(paper=self))
			return None

		self.logger.info('[SUCCESS] get pdf url of {paper}'
		                 .format(paper=self))
		return (pdf_url[0] if pdf_url[0].startswith('https://')
		                    else url_join('https://aaai.org', pdf_url[0])).replace('/view/', '/download/')

	def get_author_keywords(self):
		''' get paper author keywords

		Returns:
			str: paper author keywords if success, None otherwise
		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get author keywords of {paper}, for no _element_tree'
			                    .format(paper=self))
			return None

		author_keywords_xpath = '//meta[@name="keywords"]/attribute::content'

		author_keywords = self._element_tree.xpath(author_keywords_xpath)
		if len(author_keywords) <= 0:
			self.logger.warning('[FAIL] get author keywords of {paper}, for no author keywords, or maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		self.logger.info('[SUCCESS] get author keywords of {paper}'
		                 .format(paper=self))

		return [author_keyword.strip()
		        for author_keyword in author_keywords[0].split(';')]

	def get_authors(self):
		if self._element_tree is None:
			self.logger.warning('[FAIL] get authors of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		author_metas_xpath = '/html/head/meta[@name="citation_author" or @name="citation_author_institution" or @name="citation_author_email"]'

		author_metas = self._element_tree.xpath(author_metas_xpath)
		if len(author_metas) <= 0:
			self.logger.warning('[FAIL] get authors of {paper}, for no authors, or maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		try:
			author_infos = []
			author_metas_len = len(author_metas)
			i = 0
			while i < author_metas_len:
				# author name标签
				if author_metas[i].get('name').strip() == 'citation_author':
					author_info = {
						'affiliations': [],
						'email': '',
					}
					author_info['name'] = author_metas[i].get('content').strip()
					i += 1
					# 遍历author name标签下面的affiliation和email标签
					while i < author_metas_len:
						if author_metas[i].get('name').strip() == 'citation_author':
							author_infos.append(author_info)
							break
						if author_metas[i].get('name').strip() == 'citation_author_institution':
							author_info['affiliations'].append(author_metas[i].get('content').strip())
							i += 1
							continue
						if author_metas[i].get('name').strip() == 'citation_author_email':
							author_info['email'] = author_metas[i].get('content').strip()
							i += 1
							continue
					if i == author_metas_len:
						# append最后一个author
						author_infos.append(author_info)
				else:
					i += 1
		except:
			self.logger.warning('[FAIL] get authors of {paper}, maybe the xpath is wrong'
			                    .format(paper=self), exc_info=True)
			return None

		for i in range(len(author_infos)):
			author_infos[i]['publish_affiliation'] = ' and '.join(author_infos[i]['affiliations'])
			del author_infos[i]['affiliations']
			author_infos[i]['order'] = i+1

		self.logger.info('[SUCCESS] get authors of {paper}'
		                 .format(paper=self))
		return author_infos


if __name__ == '__main__':
	pass