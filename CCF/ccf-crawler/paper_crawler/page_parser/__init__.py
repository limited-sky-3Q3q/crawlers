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
"""
__author__ = 'lance'


from .page_parser import PageParser
from .ieee import Ieee
from .acm import Acm
from .springer import Springer
from .elsevier import Elsevier
from .aaai import Aaai
from .usenix import Usenix
from .aminer import Aminer
from .researchgate import Researchgate