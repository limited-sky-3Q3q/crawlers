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


paper = {
	# 从dblp可以获取的信息
	'_id': str, # 使用dblp中的key作为主码, 因为获取的id值可能会变
	'title': str,
	'year': str, # 年份
	'start_page': str,
	'end_page': str,
	'type': str, # 'Journal Articles' or 'Conference and Workshop Papers'
	'venue': str, # 会议\期刊的缩写
	'volume': str, # journal的volume
	'number': str, # journal的number
	'doi': str, # doi
	'venue_key': str, # 该论文所属的proceedings或volume在dblp中的key，用来区分该论文属于哪个会议\期刊

	'urls': list, # 论文的链接
	'pdf_url': str, # 论文的pdf链接
	'abstract': { # 摘要
		'source': 'eg. Ieee, Acm', # 来源
		'abstract': str
	},
	'author_keywords': { # 作者打的关键词
		'source': 'eg. Ieee, Acm',
		'author_keywords': list
	},
	# FIXME 引用与被引用都未被处理过，不同网站获取的格式都不一样，或许能从wos里面获取
	'references': {
		'source': 'eg. Ieee, Acm',
		'references': dict or list,
	},
	'citations': {
		'source': 'eg. Ieee, Acm',
		'citations': dict or list,
	},

	'authors': {
		'source': 'eg. Ieee, Acm',
		'authors': [
			{
				'_id': str, # 作者在数据库中的主码
				'name': str,
				'affiliation': str, # 作者发表这篇论文时的单位
				'order': int, # 作者顺序
			}
		]
	}
}

author = {
	'_id': str, # 在dblp中的pid，作为主码
	'dblp_name': str, # 在dblp中获取的名字，也可以作为主码
	'orcid': str, # 也可以作为主码

	'name': str,
	'first_name': str,
	'last_name': str,
	'email': str,
	'photo_url': str, # 头像图片地址
	'affiliations': list, # 作者的单位历史，当碰到已有作者时，将新地址、新链接输入
	'urls': list, # 作者页面地址
}



if __name__ == '__main__':
	pass