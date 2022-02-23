# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""module description

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

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
__author__ = 'lance'


from .mylogger import root, Logger
from .crawler import PaperCrawler


class Paper(object):
	'''class description

	Attributes:

	'''

	def __init__(self, title, url=None, logger=root):
		'''

		Args:
			title (str): paper title
			url (str or list of str): paper urls, maybe a url or multiple urls.
				Defaults to None.
			logger (Logger): logging. Defaults to root
		'''

		self.title = title
		self.url = url
		self.logger = logger

		#: str: paper abstract. Defaults to None.
		self._abstract = None

		#: list of dict: paper authors' info. Defaults to None.
		self._authors = None

		#: str: paper pdf download address. Defaults to None.
		self._pdf_url = None

		#: list of dict: paper references. Defaults to None.
		self._references = None

		#: list of dict: paper citations. Defaults to None.
		self._citations = None

		#: PaperCrawler: paper crawler
		self.crawler = PaperCrawler(title, url, logger)

	@property
	def abstract(self):
		'''str or None: return paper abstract if can get paper's abstract,
		None otherwise.
		'''
		return self.crawler.get_abstract()

	@property
	def pdf_url(self):
		'''str or None: return paper pdf download address if can get paper's pdf_Url,
		None otherwise.
		'''
		return self.crawler.get_pdf_url()

	@property
	def authors(self):
		'''list of dict or None: return paper authors' info if can get authors's info,
		None otherwise
		'''
		return self.crawler.get_authors()

	@property
	def references(self):
		'''list of dict or None: return paper references if can get paper's references,
		None otherwise
		'''
		return self.crawler.get_references()

	@property
	def citations(self):
		'''list of dict or None: return paper citations if can get paper's citations,
		None otherwise
		'''
		return self.crawler.get_citations()

	@property
	def author_keywords(self):
		'''list of str or None: return author keywords of this paper if can get it,
		None otherwise
		'''
		return self.crawler.get_author_keywords()


if __name__ == '__main__':
	pass