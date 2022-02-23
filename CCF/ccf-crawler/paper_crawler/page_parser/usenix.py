# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""parser page from `Usenix`_

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

.. _Usenix:
   https://www.usenix.org/

"""
__author__ = 'lance'


from .page_parser import PageParser
from ..mylogger import Logger, root


class Usenix(PageParser):
	def __init__(self, title: str, response, logger: Logger=root):
		super().__init__(title, response, logger)

	def get_abstract(self):
		''' get paper abstract

		Returns:
			str: paper abstract if success, None otherwise
		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get abstract of {paper}, for no _element_tree'
			                    .format(paper=self))
			return None

		abstracts_xpath = '//div[contains(text(), "Abstract")]/..//div[@class="field-items"]//p/text()'

		abstracts = self._element_tree.xpath(abstracts_xpath)
		if len(abstracts) <= 0:
			self.logger.warning('[FAIL] get abstract of {paper}, for no '
			                    'abstract, or maybe the xpath is wrong'.format(paper=self))
			return None

		self.logger.info('[SUCCESS] get abstract of {paper}'
		                 .format(paper=self))
		return ' '.join(abstracts)

	def get_pdf_url(self):
		return None

	def get_author_keywords(self):
		return None

	def get_references(self):
		return None

	def get_citations(self):
		return None

	def get_authors(self):
		if self._element_tree is None:
			self.logger.warning('[FAIL] get authors of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		# authors_xpath = '/html/head/meta[@name="citation_author"]'
		# author_affiliation_xpath = './following-sibling::meta[position() <= 2][@name="citation_author_institution"]'
		# author_email_xpath = './following-sibling::meta[position() <= 2][@name="citation_author_email"]'

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
			author_infos[i]['order'] = i+1
			del author_infos[i]['affiliations']

		self.logger.info('[SUCCESS] get authors of {paper}'
		                 .format(paper=self))
		return author_infos	
	

if __name__ == '__main__':
	pass