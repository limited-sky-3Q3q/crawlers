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


import time
from multiprocessing import Process
import psutil

from paper_crawler.crawler_manager import CrawlerManager
from paper_crawler.mylogger import  root
from settings import MAX_MEM


def run_crawler_process(target):
	'''

	Args:
		target: 需要执行的爬虫函数

	Returns:

	'''	
	try:
		process = Process(target=target, name='crawler_process')
		process.start()
		root.info('Start crawler')
		return process
	except:
		root.error('Fail start crawler process', exc_info=True)


def kill_crawler_process(crawler_process: Process):
	try:
		crawler_process.terminate()
		root.info('kill crawler process')
		return None
	except:
		root.warning('Fail kill crawler process', exc_info=True)


def run_watcher_process(target):
	'''

	Args:
		target: 需要执行的爬虫函数

	Returns:

	'''
	crawler_process = None
	while True:
		if crawler_process is None:
			crawler_process = run_crawler_process(target)
		try:
			process = psutil.Process(crawler_process.pid)
			mem = process.memory_info()[0] / float(2 ** 20)
			print(mem)
			if mem >= MAX_MEM:
				root.error('crawler process takes over memory')
				crawler_process = kill_crawler_process(crawler_process)
		except:
			root.error('something error', exc_info=True)
		time.sleep(3)


def save_dblp_papers():
	'''

	:return:
	'''
	watcher_process = Process(target=run_watcher_process, name='watcher_process',
	                          args=(CrawlerManager().save_dblp_papers,))
	watcher_process.start()
	watcher_process.join()


def solve_papers():
	'''

	:return:
	'''
	watcher_process = Process(target=run_watcher_process, name='watcher_process',
	                          args=(CrawlerManager().solve_papers,))
	watcher_process.start()
	watcher_process.join()


if __name__ == '__main__':
	# save_dblp_papers()
	solve_papers()
