# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""parser page from `Springer`_

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

.. _Springer:
   https://link.springer.com

"""
__author__ = 'lance'


from .page_parser import PageParser
from ..mylogger import Logger, root
from ..utils import url_join


class Springer(PageParser):
	TYPE = [
		'article',
		'chapter',
	]

	def __init__(self, title: str, response, logger: Logger=root):
		super().__init__(title, response, logger)

		self.type = self.real_url.replace('https://link.springer.com/', '').split('/')[0]
		if self.type not in self.TYPE:
			self.logger.warning('new type paper of https://link.springer.com, new_type: {type}'
			                    .format(type=self.type))

	def get_abstract(self):
		''' get paper abstract

		Returns:
			str: paper abstract if success, None otherwise
		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get abstract of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		if self.type == 'chapter':
			xpath = '//section[@class="Abstract"]/p'
		elif self.type == 'article':
			xpath = '//div[@id="Abs1-content"]/p'
		else:
			xpath = ''

		abstract_paras = self._element_tree.xpath(xpath)

		if len(abstract_paras) <= 0:
			self.logger.warning('[FAIL] get abstract of {paper}, maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		# 段落
		paras = []
		# 拼接每一个段落内部
		for abstract_para in abstract_paras:
			texts = abstract_para.xpath('.//text()')
			paras.append(''.join(texts))

		abstract = ' '.join(paras)

		self.logger.info('[SUCCESS] get abstract of {paper}'
		                 .format(paper=self))
		return abstract

	def get_citations(self):
		self.logger.warning('[FAIL] get citations of {paper}, for can not get citations from Springer'
		                    .format(paper=self))
		return None

	def get_references(self):
		''' get paper references

		Returns:
			:obj: `list` of :obj: 'dict': paper references if success, None otherwise.
		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get references of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		if self.type == 'chapter':
			reference_tag_xpath = '//div[@class="CitationContent"]'
		elif self.type == 'article':
			reference_tag_xpath = '//li[@itemprop="citation"]'
		else:
			reference_tag_xpath = ''

		reference_tags = self._element_tree.xpath(reference_tag_xpath)
		if len(reference_tags) <= 0:
			self.logger.warning('[FAIL] get references of {paper}, maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		references = []

		if self.type == 'chapter':
			try:
				for reference_tag in reference_tags:
					reference = {}
					texts = reference_tag.xpath('.//text()')
					reference['links'] = []

					link_tags_xpath = './/a[contains(@class, "gtm-reference")]'
					link_tags = reference_tag.xpath(link_tags_xpath)
					link_types = []
					for link_tag in link_tags:
						link = {}
						link['type'] = link_tag.xpath('./attribute::data-reference-type')[0]
						link_types.append(link['type'])
						link['link'] = link_tag.xpath('./attribute::href')[0]
						reference['links'].append(link)

					reference['text'] = ''.join([text if text not in link_types else '' for text in texts]).strip()
					references.append(reference)
			except:
				self.logger.warning('something error', exc_info=True)
				return None
		elif self.type == 'article':
			try:
				for reference_tag in reference_tags:
					reference = {}
					meta_tags = reference_tag.xpath('./meta')
					for meta_tag in meta_tags:
						reference[meta_tag.xpath('./attribute::itemprop')[0]] = meta_tag.xpath('./attribute::content')[0]

					reference['text'] = ''.join(reference_tag.xpath('./p[@class="c-article-references__text"]//text()'))

					link_tags = reference_tag.xpath('./p[contains(@class, "c-article-references__links u-hide-print")]/a')
					reference['links'] = []
					for link_tag in link_tags:
						link = {}
						link['type'] = link_tag.text.strip()
						link['link'] = link_tag.get('href').strip()
						reference['links'].append(link)

					references.append(reference)
			except:
				self.logger.warning('something error', exc_info=True)
				return None

		self.logger.info('[SUCCESS] get references of {paper}'
		                 .format(paper=self))
		return references

	def get_pdf_url(self):
		''' get paper pdf url

		Returns:
			str: paper pdf url if success, None otherwise

		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get pdf_url of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		xpath = '//meta[@name="citation_pdf_url"]/attribute::content'

		base_url = 'https://link.springer.com'
		pdf_url = self._element_tree.xpath(xpath)
		if len(pdf_url) <= 0:
			self.logger.warning('[FAIL] get pdf_url of {paper}, for no pdf, or maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		pdf_url = pdf_url[0]
		if not pdf_url.startswith('https'):
			pdf_url = url_join(base_url, pdf_url)

		self.logger.info('[SUCCESS] get pdf_url of {paper}'
		                 .format(paper=self))
		return pdf_url

	def get_authors(self):
		''' get authors' info

		Returns:
			:obj: `list` of :obj: 'dict': paper authors' info if success, None otherwise.
		'''
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
			author_infos[i]['order'] = i + 1
			del author_infos[i]['affiliations']

		self.logger.info('[SUCCESS] get authors of {paper}'
		                 .format(paper=self))
		return author_infos

	def get_author_keywords(self):
		''' get author keywords

		Returns:
			list: author keywords if success, None otherwise
		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get author-keywords of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		XPATH_CHAPTER = '//span[@class="Keyword"]/text()'
		XPATH_ARTICLE = '//ul[@class="c-article-subject-list"]/li/span/text()'

		if self.type == 'article':
			xpath = XPATH_ARTICLE
		elif self.type == 'chapter':
			xpath = XPATH_CHAPTER
		else:
			return None

		keywords = self._element_tree.xpath(xpath)
		if len(keywords) <= 0:
			self.logger.warning('[FAIL] get author-keywords of {paper}, for no author-keywords'
			                    .format(paper=self))
			return None

		self.logger.info('[SUCCESS] get author-keywords of {paper}'
		                 .format(paper=self))
		return [keyword.strip() for keyword in keywords]


if __name__ == '__main__':
	pass