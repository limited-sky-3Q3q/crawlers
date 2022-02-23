# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""page_parser superclass

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

"""
__author__ = 'lance'


from lxml import etree
from abc import abstractmethod, ABCMeta
from requests import Response
from ..mylogger import Logger, root


class PageParser(metaclass=ABCMeta):

	def __init__(self, title, response, logger=root):
		'''

		Args:
			title (str): paper title
			response (Response):
			logger (Logger): logging. Defaults to root
		'''
		self.title = title
		self.response = response
		self.logger = logger

		#: str: page url
		self.real_url = response.url

		#: Element: page's element tree
		self._element_tree = self._get_element_tree()

	def __str__(self):
		return ('<Paper, title: {title}, url: {url}>'
		        .format(title=self.title, url=self.real_url))

	def _get_element_tree(self):
		'''parser html page into Element tree, then get info from
		Element tree by xpath.

		Returns:
			Element, None: Element tree if success, None otherwise.

		'''
		try:
			element_tree = etree.HTML(self.response.text)
		except:
			self.logger.warning('Fail get parser page of <Paper, title: {title}, url: {url}>'
			                    .format(title=self.title, url=self.real_url), exc_info=True)
			return None

		return element_tree

	@abstractmethod
	def get_abstract(self):
		pass

	@abstractmethod
	def get_pdf_url(self):
		pass

	@abstractmethod
	def get_authors(self):
		pass

	@abstractmethod
	def get_references(self):
		pass

	@abstractmethod
	def get_citations(self):
		pass

	@abstractmethod
	def get_author_keywords(self):
		pass