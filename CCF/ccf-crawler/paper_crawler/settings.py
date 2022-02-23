
# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""module description

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


# 是否启用proxy
PROXY_POOL_ENABLE = False

# proxy pool的地址
PROXY_API_HOST = 'http://106.53.93.41'
PROXY_API_PORT = '5010'

# mongodb的地址
MONGODB_HOST = '47.115.47.28'
# mongodb的端口号，数据库默认是27017
MONGODB_PORT = 27017
# mongodb账户名
USER = 'lance'
# 密码
PWD = 'lance159753*'

# 线程数量
TH_NUM = 1

# 处理论文记录存放位置
RECORDS_PATH = './records/'
