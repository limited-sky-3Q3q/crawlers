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


import json
from pymongo import MongoClient

from .mylogger import Logger, root
from .utils import singleton
from .settings import MONGODB_HOST, MONGODB_PORT, USER, PWD


@singleton
class Client():
	# 数据库名字
	DB_NAME = 'ccf'

	def __init__(self, *, user: str=USER, pwd: str=PWD, host: str=MONGODB_HOST,
	             port: str or int=MONGODB_PORT, db_name: str=None, logger: Logger=root):
		if not user:
			url = 'mongodb://{host}:{port}'.format(host=host, port=port)
		else:
			url = 'mongodb://{user}:{pwd}@{host}:{port}'.format(user=user, pwd=pwd, host=host, port=port)

		self.logger = logger
		self.client = MongoClient(url)
		# 数据库
		self.db = self.client[db_name or self.DB_NAME]
		# paper集合
		self.paper_coll = self.db.paper_coll
		# author集合
		self.author_coll = self.db.author_coll

	def __insert_one(self, coll, document: dict):
		return coll.insert_one(document)

	# TODO test
	def insert_one_paper(self, paper_dict: dict):
		return self.__insert_one(self.paper_coll, paper_dict)

	# TODO test
	def insert_one_author(self, author_dict: dict):
		return self.__insert_one(self.author_coll, author_dict)


	def __find_one(self, coll, query_dict: dict, project: dict=None):
		return coll.find_one(query_dict, project)

	# TODO test
	def find_one_paper(self, query_dict: dict, project: dict=None):
		project = project or {
			'raw_citations': 0,
			'raw_references': 0
		}
		return self.__find_one(self.paper_coll, query_dict, project)

	# TODO test
	def find_one_author(self, query_dict: dict, project: dict=None):
		return self.__find_one(self.author_coll, query_dict, project)

	def __update_one(self, coll, query_dict: dict, update_dict: dict, upsert: bool=False):
		return coll.update_one(query_dict, update_dict, upsert=upsert)

	# TODO test
	def update_one_paper(self, query_dict: dict, update_dict: dict):
		return self.__update_one(self.paper_coll, query_dict, update_dict)

	# TODO test
	def update_one_author(self, query_dict: dict, update_dict: dict):
		return self.__update_one(self.author_coll, query_dict, update_dict)

	# TODO test
	def add_one_paper(self, query_dict: dict, update_dict: dict):
		return self.__update_one(self.paper_coll, query_dict, update_dict, upsert=True)

	# TODO test
	def add_one_author(self, query_dict: dict, update_dict: dict):
		return self.__update_one(self.author_coll, query_dict, update_dict, upsert=True)

	def _remove_one(self, coll, query_dict):
		return coll.remove(query_dict)

	def remove_one_author(self, query_dict: dict):
		return self._remove_one(self.author_coll, query_dict)

	def remove_one_paper(self, query_dict: dict):
		return self._remove_one(self.paper_coll, query_dict)

	def get_co_authors(self, author_id: str):
		''' 获取单个作者的co-authors

		:param author_id:
		:return:
		'''
		papers = self.paper_coll.find({ 'authors._id': author_id },
		                            { 'authors': 1 })

		co_authors_dict = {}

		for paper in papers:
			co_authors = paper['authors']
			for co_author in co_authors:
				co_author_id = co_author['_id']
				if co_author_id != author_id:
					if co_author_id not in co_authors_dict.keys():
						co_authors_dict[co_author_id] = 0

					co_authors_dict[co_author_id] += 1

		# print(json.dumps(co_authors_dict, indent=4))
		co_authors = [
			{
				'_id': key,
				'num': value,
			}
			for key, value in co_authors_dict.items()
		]
		# print(json.dumps(co_authors, indent=4))

		return co_authors

	def get_all_co_authors(self):
		''' 获取所有作者的co-authors

		:return:
		'''
		authors = self.author_coll.find({})
		all_co_authors_dict = {}

		for author in authors:
			all_co_authors_dict[author['_id']] = self.get_co_authors(author['_id'])

		# print(json.dumps(all_co_authors_dict, indent=4))

		return all_co_authors_dict

	def get_paper_references(self, paper_id: str):
		''' 获取论文的引用

		:param paper_id:
		:return:
		'''
		paper = self.find_one_paper({'_id': paper_id}, {'references': 1})
		if paper is None:
			return None

		return paper['references']

	def get_all_paper_references(self):
		''' 获取所有论文的references

		:return:
		'''
		papers = self.paper_coll.find({}, {'references': 1})
		all_references = {}
		for paper in papers:
			all_references[paper['_id']] = paper['references']

		return all_references

	def get_paper_citations(self, paper_id: str):
		''' 获取论文的citations

		:return:
		'''
		paper = self.find_one_paper({'_id': paper_id}, {'citations': 1})
		if paper is None:
			return None

		return paper['citations']

	def get_all_paper_citations(self):
		''' 获取所有论文的citations

		:return:
		'''
		papers = self.paper_coll.find({}, {'citations': 1})
		all_citations = {}
		for paper in papers:
			all_citations[paper['_id']] = paper['citations']

		return all_citations

	def get_all_papers(self):
		''' 获取所有论文的title、 abstract、 author keywords

		:return:
		'''
		# papers = self.paper_coll.find({}, {'_id': 0, 'year': 1, 'title': 1, 'abstract': 1, 'author_keywords': 1})
		papers = self.paper_coll.find({}, {'title': 1, 'authors': 1}, no_cursor_timeout=True).batch_size(100)
		return papers

	def get_unsolved_papers(self):
		''' 获取未被处理的论文, 一次返回100个

		Returns:

		'''
		return self.paper_coll.find({'solved': None}, no_cursor_timeout=True).batch_size(100)


if __name__ == '__main__':
	pass