# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""my requests module

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


import requests

from .settings import PROXY_POOL_ENABLE
from .mylogger import root, Logger
from .proxy import requests_get_with_proxy, requests_post_with_proxy, ProxySession
from .utils import requests_get, requests_post, session_get, session_post


def get(url: str, *, website: str='', tries: int=3, success_wait: int=0, logger: Logger=root,
        wait_random_min: int=10, wait_random_max: int=30, **kwargs):
	if PROXY_POOL_ENABLE:
		return requests_get_with_proxy(url, website=website, logger=logger, **kwargs)
	else:
		return requests_get(url, tries=tries, logger=logger, success_wait=success_wait,
		                    wait_random_min=wait_random_min, wait_random_max=wait_random_max, **kwargs)


def post(url: str, *, website: str='', tries: int=3, success_wait: int=0, logger: Logger=root,
         wait_random_min: int=10, wait_random_max: int=30, **kwargs):
	if PROXY_POOL_ENABLE:
		return requests_post_with_proxy(url, website=website, logger=logger, **kwargs)
	else:
		return requests_post(url, tries=tries, logger=logger, success_wait=success_wait,
		                     wait_random_min=wait_random_min, wait_random_max=wait_random_max, **kwargs)


class Session():
	def __init__(self, website: str='', logger: Logger=root):
		if PROXY_POOL_ENABLE:
			self.s = ProxySession(website=website, logger=logger)
		else:
			self.s = requests.session()

		self.logger = logger

	def get(self, url: str, *, tries: int=3, success_wait: int=0, logger: Logger=root,
	        wait_random_min: int=10, wait_random_max: int=30, timeout: int=30, **kwargs):
		if PROXY_POOL_ENABLE:
			return self.s.get(url, timeout=timeout, **kwargs)
		else:
			return session_get(self.s, url, tries=tries, success_wait=success_wait,
			                   logger=logger, wait_random_min=wait_random_min,
			                   wait_random_max=wait_random_max, timeout=timeout, **kwargs)

	def post(self, url: str, *, tries: int=3, success_wait: int=0, logger: Logger=root,
	        wait_random_min: int=10, wait_random_max: int=30, timeout: int=30, **kwargs):
		if PROXY_POOL_ENABLE:
			return self.s.post(url, timeout=timeout, **kwargs)
		else:
			return session_post(self.s, url, tries=tries, success_wait=success_wait,
			                   logger=logger, wait_random_min=wait_random_min,
			                   wait_random_max=wait_random_max, timeout=timeout, **kwargs)


if __name__ == '__main__':
	pass