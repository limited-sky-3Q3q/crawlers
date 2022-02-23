# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""paper crawler module

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

"""

__author__ = 'lance'

NEW_WEBSITE_FILE_PATH = './new_website.txt'


from lxml import etree

from .mylogger import Logger, root
from .page_parser import Ieee, Acm, Aminer, Aaai, Elsevier, Researchgate, Springer, Usenix
from .utils import random_user_agent, url_join, write
from .myrequests import get


class PaperCrawler(object):

	def __init__(self, title, url, logger=root):
		'''

		Args:
			title (str): paper title.
			url (str or list of str): paper urls, maybe a url or multiple urls.
			logger (Logger): logging. Defaults to root
		'''
		self.title = title
		self.url = url
		self.logger = logger

		#: PageParser: page parser.
		self.page_parser = self._get_page_parser()

	def __str__(self):
		return ('<Paper, title: {title}, url: {url}>'
		        .format(title=self.title, url=self.real_url))

	def _get_page_parser(self):
		''' get page_parser

		Returns:
			PaperParser, None: paper's page parser if page parser exists,
				None otherwise.

		'''
		headers = {
			'user-agent': random_user_agent(),
			# 'Upgrade-Insecure-Requests': '1',
			# 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
		}

		# 全是https的，某些aaai的论文会给到http的无效链接
		url = self.url.replace('http://www.aaai.org/', 'https://www.aaai.org/')\
				.replace('http://aaai.org/', 'https://aaai.org/')

		# 空连接或者pdf链接
		if not url or (url.startswith('http://ceur-ws.org/') and url.endswith('.pdf')):
			self.logger.warning('url not exists')
			return None

		# 优先选择Ieee
		if url.startswith('https://ieeexplore.ieee.org/'):
			website = 'ieee'
			response = get(url, headers=headers, website=website)
			if response is not None:
				return Ieee(self.title, response, logger=self.logger)

		# 在IEEE中搜索到该paper
		# FIXME ieee代理发送post请求返回415，貌似代理被封
		ieee_search_result = Ieee.search_by_title(self.title, logger=self.logger)
		if ieee_search_result and 'documentLink' in ieee_search_result:
			new_url = url_join('https://ieeexplore.ieee.org/', ieee_search_result['documentLink'])
			response = get(new_url, website='ieee', headers=headers, logger=self.logger)
			if response is not None:
				return Ieee(self.title, response, logger=self.logger)

		# 在Acm中搜索
		acm_search_result = Acm.search_by_title(self.title, logger=self.logger)
		if acm_search_result:
			response = get(acm_search_result, website='acm', headers=headers, logger=self.logger)
			if response is not None:
				return Acm(self.title, response, logger=self.logger)

		# 在Elsevier中搜索
		sciencedirect_search_result = Elsevier.search_by_title(self.title, logger=self.logger)
		if sciencedirect_search_result is not None:
			new_url = sciencedirect_search_result
			response = get(new_url, website='sciencedirect', headers=headers, logger=self.logger)
			if response:
				return Elsevier(self.title, response, logger=self.logger)

		if url.startswith('https://dl.acm.org/'):
			website = 'acm'
		elif url.startswith('https://www.sciencedirect.com/'):
			website = 'sciencedirect'
		elif url.startswith('https://link.springer.com/'):
			website = 'springer'
		elif url.startswith('https://aaai.org/') or url.startswith('https://www.aaai.org'):
			website = 'aaai'
		elif url.startswith('https://www.usenix.org/') or url.startswith('https://usenix.org/'):
			website = 'usenix'
		elif url.startswith('https://www.researchgate.net/'):
			website = 'researchgate'
		elif url.startswith('https://www.aminer.cn/'):
			website = 'aminer'
		else:
			website = 'doi'

		# FIXME 暂时处理doi链接重定向后链接值无效地址（eg: https://doi.org/10.1609/aaai.v33i01.33015660)
		allow_redirects = True
		if url.find('https://doi.org/') == 0 and 'aaai' in url:
			allow_redirects = False


		response = get(url, website=website, headers=headers,
		               allow_redirects=allow_redirects, logger=self.logger)
		if response is not None:
			real_url = response.url

			# FIXME 暂时处理doi链接重定向后链接值无效地址（eg: https://doi.org/10.1609/aaai.v33i01.33015660)
			if real_url.find('https://doi.org') == 0:
				doi_element_tree = etree.HTML(response.content)
				try:
					doi_redirect_url = doi_element_tree.find('.//a').get('href')\
						.replace('https://aiide.org', 'https://aaai.org')\
						.replace('https://aimagazine.org', 'https://aaai.org')\
						.replace('https://wvvw.aaai.org', 'https://aaai.org')\
						.replace('144.208.67.177', 'aaai.org')
					doi_response = get(doi_redirect_url, website='aaai', headers=headers, logger=self.logger)
					real_url = doi_response.url
					response = doi_response
				except:
					self.logger.error('doi redirect error', exc_info=True)

			# 直接判断为IEEE
			if real_url.find('https://ieeexplore.ieee.org/') == 0:
				return Ieee(self.title, response, logger=self.logger)

			# elsevier重定向到sciencedirect
			if real_url.find('https://linkinghub.elsevier.com') == 0:
				redirect_url_xpath = '//meta[@http-equiv="REFRESH"]/attribute::content'
				element_tree = etree.HTML(response.text)
				try:
					# get redirect url
					redirect_url = element_tree.xpath(redirect_url_xpath)[0]
					redirect_url = redirect_url[redirect_url.find('url=')+4:].replace('\'', '')
					new_url = url_join('https://linkinghub.elsevier.com', redirect_url)
				except:
					self.logger.warning('[FAIL] get redirect url of {url}'
					               .format(url=real_url), exc_info=True)
				else:
					# response = requests_get(new_url, headers=headers)
					response = get(new_url, website='sciencedirect', headers=headers, logger=self.logger)
					if response is None:
						self.logger.warning('[FAIL] get page parser of <{title}>, for fail get the redirect url {new_url}'
						               .format(title=self.title, new_url=new_url))
					real_url = response.url

			# SCIENCEDIRECT
			if real_url.find('https://www.sciencedirect.com') == 0:
				return Elsevier(self.title, response, logger=self.logger)

			# ACM
			if real_url.find('https://dl.acm.org/') == 0:
				return Acm(self.title, response, logger=self.logger)

			# SPRINGER
			if real_url.find('https://link.springer.com/') == 0:
				return Springer(self.title, response, logger=self.logger)

			# AAAI
			if real_url.find('https://aaai.org/') == 0 or real_url.find('https://www.aaai.org') == 0:
				return Aaai(self.title, response, logger=self.logger)

			# USENIX
			if real_url.find('https://www.usenix.org/') == 0 or real_url.find('https://usenix.org/') == 0:
				return Usenix(self.title, response, logger=self.logger)

			if real_url.find('https://www.researchgate.net/') == 0:
				return Researchgate(self.title, response, logger=self.logger)

			if real_url.find('https://www.aminer.cn/') == 0:
				return Aminer(self.title, response, logger=self.logger)

		# 在searchgate中搜索
		searchgate_search_result = Researchgate.search_by_title(self.title, logger=self.logger)
		if searchgate_search_result:
			response = get(searchgate_search_result, website='researchgate', headers=headers, logger=self.logger)
			if response:
				return Researchgate(self.title, response, logger=self.logger)

		# 在Aminer中搜索
		aminer_search_result = Aminer.search_by_title(self.title, logger=self.logger)
		if aminer_search_result:
			response = get(aminer_search_result, website='aminer', headers=headers, logger=self.logger)
			if response:
				return Aminer(self.title, response, logger=self.logger)

		self.logger.warning('[FAIL] get page parser of paper <{title}, {url}>'
		               .format(title=self.title, url=url))
		write(url + '\n', NEW_WEBSITE_FILE_PATH, 'a', logger=self.logger)
		return None

	@property
	def real_url(self):
		'''str or None: return paper real url (after redirect) if page
		parser exists, None otherwise.
		'''
		return self.page_parser.real_url if self.page_parser is not None else None

	@property
	def page_parser_name(self):
		return self.page_parser.__class__.__name__ if self.page_parser is not None else None

	def get_abstract(self):
		'''get paper abstract

		Returns:
		 	dict: paper abstract if page parser exists and
		 	    paper abstract exists, None otherwise.

			Examples:
				{
					"source": "Ieee",
					"abstract": '...'
				}
		'''
		abstract = self.page_parser.get_abstract() if self.page_parser is not None else None
		if abstract is not None:
			return {
				"source": self.page_parser_name,
				"abstract": abstract
			}

		return None

	def get_pdf_url(self):
		'''get paper pdf url

		Returns:
			str, None: paper pdf download address if page parser exists
				and can get paper pdf url correctly, None otherwise.

		'''
		return self.page_parser.get_pdf_url() if self.page_parser is not None else None

	def get_authors(self):
		'''get paper authors' info

		Returns:
			dict: paper authors' info if page parser
				exists and can get paper authors' info correctly, None otherwise.

			Examples:
				{
					"source": "Ieee",
					"authors": [...]
				}
		'''
		authors = self.page_parser.get_authors() if self.page_parser is not None else None
		if authors is not None:
			return {
				"source": self.page_parser_name,
				"authors": authors
			}
		return None

	def get_references(self):
		'''get paper references

		Returns:
			:obj:`list` of :obj:`dict`, None: paper references if page parser
				exists and can get paper references correctly, None otherwise.

		'''
		references = self.page_parser.get_references() if self.page_parser is not None else None
		if references is not None:
			return {
				"source": self.page_parser_name,
				"references": references
			}

		return None

	def get_citations(self):
		'''get paper citations

		Returns:
			:obj:`list` of :obj:`dict`, None: paper citations if page parser
				exists and can get paper citations correctly, None otherwise.

		'''
		citations = self.page_parser.get_citations() if self.page_parser is not None else None
		if citations is not None:
			return {
				"source": self.page_parser_name,
				"citations": citations
			}

		return None

	def get_author_keywords(self):
		'''get author keywords of paper

		Returns:
			:obj: `list` of :obj:`str`, None: paper author keywords if page parser
				exists and can get paper author keywords correctly, None otherwise.

		'''
		author_keywords = self.page_parser.get_author_keywords() if self.page_parser is not None else None
		if author_keywords is not None:
			return {
				"source": self.page_parser_name,
				"author_keywords": author_keywords
			}

		return None

	# TODO test
	def get_aminer_keywords(self):
		headers = {
			'user-agent': random_user_agent(),
		}

		aminer_search_result = Aminer.search_by_title(self.title, logger=self.logger)
		if aminer_search_result:
			response = get(aminer_search_result, website='aminer', headers=headers, logger=self.logger)
			if response is None:
				self.logger.warning('[FAIL] get aminer keywords of {paper}'
				                    .format(paper=self))
				return None

			aminer_paper = Aminer(self.title, response, logger=self.logger)
			aminer_keywords = aminer_paper.get_keywords()
			return aminer_keywords

if __name__ == '__main__':
	pass