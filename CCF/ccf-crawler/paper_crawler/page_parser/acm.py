# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""parser page from `ACM`_

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

.. _ACM:
   https://dl.acm.org

"""

__author__ = 'lance'


from lxml import etree

from ..utils import url_join, random_user_agent
from .page_parser import PageParser
from ..myrequests import Session, get
from ..mylogger import Logger, root


class Acm(PageParser):
	def __init__(self, title: str, response, logger: Logger=root):
		super().__init__(title, response, logger)

		#: str: paper article number in ACM
		self.doi = self.real_url.split('doi/')[-1]

		self.session = Session('acm', logger=logger)

	def get_abstract(self):
		''' get paper abstract

		Returns:
			str, None: paper abstract if success, None otherwise

		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get abstract of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		xpath = '//div[contains(@class, "article__section article__abstract")]//p'
		p_tags = self._element_tree.xpath(xpath)
		if len(p_tags) <= 0:
			self.logger.warning('[FAIL] get abstract of {paper}, maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		# 每个p_tag里面的文本直接拼接，所有p_tag的文本中间一个空格拼接
		abstract = ' '.join([''.join(p_tag.xpath('.//text()')) for p_tag in p_tags])
		if abstract == 'No abstract available.':
			self.logger.warning('[FAIL] get abstract of {paper}, for no abstract available'
			                    .format(paper=self))
			return None

		self.logger.info('[SUCCESS] get abstract of {paper}'
		                 .format(paper=self))
		return abstract

	# TODO test
	def get_pdf_url(self):
		''' get paper pdf url

		Returns:
			str, None: paper pdf url if success, None otherwise
		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get pdf_url of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		xpath = '//a[@title="PDF"]/attribute::href'
		base_url = 'https://dl.acm.org'
		pdf_url = self._element_tree.xpath(xpath)
		if len(pdf_url) <= 0:
			self.logger.warning('[FAIL] get pdf_url of {paper}, for no pdf, or maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		pdf_url = url_join(base_url, pdf_url[0])

		self.logger.info('[SUCCESS] get pdf_url of {paper}'
		                 .format(paper=self))
		return pdf_url

	def get_references(self):
		''' get paper references

		Returns:
			:obj: `list` of :obj: `dict`: paper references if success, None otherwise.

		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get referenes of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		xpath = '//div[contains(@class, "article__section article__references")]/ol[contains(@class, "references__list references__numeric")]/li[contains(@class, "references__item")]/span[contains(@class, "references__note")]'
		reference_tags = self._element_tree.xpath(xpath)
		if len(reference_tags) <= 0:
			self.logger.warning('[FAIL] get references of {paper}, for no references, or maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		references = []
		ref_order = 1
		for reference_tag in reference_tags:
			reference = {}
			reference['order'] = ref_order
			ref_order += 1
			reference['text'] = ''.join(reference_tag.xpath('.//text()'))\
				.replace('Digital Library', '')\
				.replace('Google Scholar', '')\
				.replace('Cross Ref', '')\
				.strip()

			reference['links'] = [
				{
					'type': ''.join(reference_suffix_tag.xpath('.//text()')),
					'link': (url_join('https://dl.acm.org', reference_suffix_tag.get('href'))
							if not reference_suffix_tag.get('href').startswith('http')
							else reference_suffix_tag.get('href'))
							.strip('.'),
				}
				for reference_suffix_tag in reference_tag.xpath('./span[contains(@class, "references__suffix")]/a')
			]
			references.append(reference)

		self.logger.info('[SUCCESS] get references of {paper}'
		                 .format(paper=self))
		return references

	# TODO bug
	def get_citations(self):
		return None

	# def get_citations(self):
	# 	''' get paper citations

	# 	Returns:
	# 		:obj: `list` of :obj: `dict`: paper citations if success, None otherwise.
	# 	'''
	# 	# 先获取citations的数量,如果为0，就直接返回None
	# 	citation_num_xpath = '//div[@class="article-metric citation"]/div[@class="metric-value"]/span/text()'
	# 	citation_num_tag = self._element_tree.xpath(citation_num_xpath)
	# 	# 无法获取到citations的数量
	# 	if len(citation_num_tag) <= 0:
	# 		self.logger.warning('[FAIL] get citations_num of {paper}, maybe the xpath is wrong'
	# 		                    .format(paper=self))
	# 	else:
	# 		citation_num = int(citation_num_tag[0])
	# 		if citation_num == 0:
	# 			self.logger.warning('[FAIL] get citations of {paper}, for no citations'
	# 			                    .format(paper=self))
	# 			return None

	# 	headers = {
	# 		'user-agent': random_user_agent(),
	# 	}
	# 	# FIXME 对于pbContext有bug
	# 	params = {
	# 		'widgetId': 'f69d88a8-b404-4aae-83a9-9acea4426d78',
	# 		'ajax': 'true',
	# 		'doi': self.doi,
	# 		# 'pbContext': ';page:string:Article/Chapter View;subPage:string:Abstract;wgroup:string:ACM Publication Websites;groupTopic:topic:acm-pubtype&gt;proceeding;csubtype:string:Conference Proceedings;topic:topic:conference-collections&gt;icpsproc;article:article:doi\:10.1145/3092627.3092632;website:website:dl-site;journal:journal:acmotherconferences;ctype:string:Book Content;issue:issue:doi\:10.1145/3092627;pageGroup:string:Publication Pages',
	# 	}
	# 	url = 'https://dl.acm.org/action/ajaxShowCitedBy'
	# 	# response = requests_get(url, headers=headers, params=params, logger=self.logger)
	# 	response = self.session.get(url, headers=headers, params=params)
	# 	if response is None:
	# 		self.logger.warning('[FAIL] get citations of {paper}, for fail get {url}, maybe the params are wrong'
	# 		                    .format(paper=self, url=url))
	# 		return None

	# 	citations_element_tree = etree.HTML(response.content)

	# 	xpath = '//*[@class="references__note"]'
	# 	citation_tags = citations_element_tree.xpath(xpath)
	# 	if len(citation_tags) <= 0:
	# 		self.logger.warning('[FAIL] get citations of {paper}, for no citations'
	# 		                    .format(paper=self))
	# 		return None

	# 	citations = []
	# 	cit_order = 1
	# 	for citation_tag in citation_tags:
	# 		citation = {}
	# 		citation['order'] = cit_order
	# 		cit_order += 1
	# 		# 整个citation的文本
	# 		text = ''.join(citation_tag.xpath('.//text()')).split('http')[0]
	# 		citation['text'] = text
	# 		# citation中的链接
	# 		link_tags = citation_tag.xpath('./p/a[@class="link"]/text()')
	# 		citation['link'] = link_tags

	# 		span_tags = citation_tag.xpath('./span')
	# 		for span_tag in span_tags:
	# 			span_tag_class = span_tag.get('class')
	# 			# authors
	# 			if span_tag_class == 'references__authors':
	# 				citation['authors'] = [
	# 					{
	# 						'name': author_tag.text,
	# 						'search_url': url_join('https://dl.acm.org', author_tag.get('href')),
	# 					}
	# 					for author_tag in span_tag.xpath('./span[@class="hlFld-ContribAuthor"]/a')
	# 				]
	# 			# seperator
	# 			elif span_tag_class == 'seperator':
	# 				continue
	# 			else:
	# 				citation[span_tag_class] = ''.join(span_tag.xpath('.//text()'))

	# 		citations.append(citation)

	# 	self.logger.info('[SUCCESS] get citations of {paper}'
	# 	                 .format(paper=self))
	# 	return citations

	def get_author_keywords(self):
		''' get paper author keywords

		Returns:
			list: author keywords if success, None otherwise

		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get author-keywords of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		xpath = '//h3[text()="Author Tags"]/following-sibling::div[1]//text()'
		author_keywords = self._element_tree.xpath(xpath)
		if len(author_keywords) <= 0:
			self.logger.warning('[FAIL] get author-keywords of {paper}, for no author-keywords'
			                    .format(paper=self))
			return None

		self.logger.info('[SUCCESS] get author-keywords of {paper}'
		                 .format(paper=self))
		return author_keywords

	def get_authors(self):
		''' get authors' info (include: id, name, order, publish_affiliation)

		Returns:
			:obj: `list` of :obj: 'dict': paper authors' info if success, None otherwise.

			Examples:
				{}
		'''
		if self._element_tree is None:
			self.logger.warning('[FAIL] get authors of {paper}, for no __element_tree'
			                    .format(paper=self))
			return None

		xpath = '//div[@class="citation"]//li[@class="loa__item"]/a/span[@class="loa__author-info"]'
		author_tags = self._element_tree.xpath(xpath)
		if len(author_tags) <= 0:
			self.logger.warning('[FAIL] get authors of {paper}, maybe the xpath is wrong'
			                    .format(paper=self))
			return None

		author_infos = []
		name_xpath = './/span[@class="loa__author-name"]/span/text()'
		id_xpath = './span[@class="loa_author_inst"]/p/attribute::data-doi'
		publish_affiliation_xpath = './span[@class="loa_author_inst"]/p/text()'
		# 获取基本信息，作者id、name、出版该论文时的单位(publish_affiliation)
		author_order = 1
		for author_tag in author_tags:
			name = author_tag.xpath(name_xpath)
			id = author_tag.xpath(id_xpath)
			publish_affiliation = author_tag.xpath(publish_affiliation_xpath)
			# TODO 获取的name不一定正确，可以在后面获取author具体信息后update
			# TODO id可能无法获取，需要通过别的途径获取（比如拿着title去search，在匹配上的result_item上获取）
			author_infos.append({
				'order': author_order,
				'id': id[0].split('contrib-')[-1].strip() if id else '',
				'name': name[0].strip() if name else '',
				'publish_affiliation': publish_affiliation[0].strip() if publish_affiliation else '',
			})
			author_order += 1

		self.logger.info('[SUCCESS] get authors of {paper}'
		                 .format(paper=self))
		return author_infos

	@classmethod
	def search_by_title(cls, title, logger: Logger=root):
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

		def __build_query(term):
			words = term.split(' ')
			query = ''.join(['+' + word for word in words])
			print(query)
			return query

		headers = {
			'user-agent': random_user_agent(),
		}
		title = title.strip()
		query_text = __build_query(title)
		# print(query_text)
		params = {
			'fillQuickSearch': 'false',
			'expand': 'all',
			'field1': 'Title',
			'text1': query_text
		}

		url = 'https://dl.acm.org/action/doSearch'
		response = get(url, website='acm', params=params, headers=headers, logger=logger)
		if response == None:
			logger.warning('[FAIL] find with title <{title}>, for network error'
			               .format(title=title))
			return None

		element_tree = etree.HTML(response.text)
		result_items_xpath = '//li[@class="search__item issue-item-container"]/div[contains(@class, "issue-item--search")]/div[@class="issue-item__content"]'
		result_items = element_tree.xpath(result_items_xpath)
		if len(result_items) <= 0:
			logger.warning('[FAIL] find with title <{title}>, for no results'
			               .format(title=title))
			return None

		result_title_xpath = './/h5[@class="issue-item__title"]/span/a//text()'
		result_url_xpath = './/h5[@class="issue-item__title"]/span/a/attribute::href'
		for result_item in result_items:
			result_title = ''.join(result_item.xpath(result_title_xpath))
			# print(result_title)
			if compare_title(title, result_title):
				result_url = result_item.xpath(result_url_xpath)
				if len(result_url) <= 0:
					logger.warning('[FAIL] find with title <{title}>, for fail get result url, maybe the xpath is wrong'
					               .format(title=title))
					return None

				logger.info('[SUCCESS] find with title <{title}>'
				            .format(title=title))
				return url_join('https://dl.acm.org', result_url[0])

		logger.warning('[FAIL] find with title <{title}>, for no matching result'
		               .format(title=title))
		return None


if __name__ == '__main__':
	pass