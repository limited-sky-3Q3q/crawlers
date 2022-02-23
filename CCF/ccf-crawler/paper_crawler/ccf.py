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

import requests
from lxml import etree

from paper_crawler.dblp import get_journals_papers, get_conf_papers
from paper_crawler.mylogger import root
from paper_crawler.utils import requests_get, url_join


# root.setLevel(50)


def decode_iso(response):
	if response.encoding == 'ISO-8859-1':
		encodings = requests.utils.get_encodings_from_content(response.text)
		if encodings:
			encoding = encodings[0]
		else:
			encoding = response.apparent_encoding
	else:
		encoding = response.encoding

	encode_content = response.content.decode(encoding, 'ignore').encode('utf-8', 'ignore')
	return encode_content


headers = {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
	'Accept-Encoding': 'gzip, deflate, br',
	'Accept-Language': 'zh-CN,zh;q=0.9',
	'Connection': 'keep-alive',
	'Cookie': '122_vq=32',
	'Host': 'www.ccf.org.cn',
	'Sec-Fetch-Mode': 'navigate',
	'Sec-Fetch-Site': 'same-origin',
	'Sec-Fetch-User': '?1',
	'Upgrade-Insecure-Requests': '1',
	'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
}


# 获取ccf所有领域
def get_domains():
	ccf_url = 'https://www.ccf.org.cn/Academic_Evaluation/By_category/'
	response = requests_get(ccf_url, headers=headers)
	if response == None:
		return

	# 解决ISO-8859-1中文乱码
	encode_content = decode_iso(response)

	element_tree = etree.HTML(encode_content)
	domain_tags = element_tree.xpath('//div[@class="snv"]/ul/li/a')
	domain_tags = domain_tags[1:]
	domain_tags.pop()
	domains = [
		{
			'name': domain_tag.get('title'),
			'url': url_join('https://www.ccf.org.cn', domain_tag.get('href')),
		}
		for domain_tag in domain_tags
	]

	# 使用json序列化会将中文编码成unicode字符串, 所以需要编码再解码处理
	print(json.dumps(domains, indent=4).encode('utf-8').decode('unicode_escape'))

	return domains


def get_journals(domain_name: str, domain_url, level: list or str or set):
	''' 获取一个领域内的某一类或多类的所有期刊\会议

	:param domain_name: 领域名，eg. "计算机体系结构/并行与分布计算/存储系统"
	:param domain_url: 该领域在ccf的url
	:param level: 类别，['A', 'B', 'C']表示获取ABC三类的会议\期刊
	:return:
	'''

	LEVEL = {
		'A': 'A类',
		'B': 'B类',
		'C': 'C类',
	}

	levels = {level} if isinstance(level, str) else set(level)
	levels = list(levels)
	levels.sort()
	response = requests_get(domain_url, headers=headers)
	if response == None:
		return

	encode_content = decode_iso(response)
	element_tree = etree.HTML(encode_content)

	journals = []
	print('{')
	print('    \'name\': \'{}\','.format(domain_name))
	print('    \'url\': \'{}\','.format(domain_url))
	print('    \'levels\': [')
	for level in levels:
		print('        {')
		print('            \'level\': \'{}\','.format(level))
		uls = element_tree.xpath('//h3[text()="{level}"]/following::ul[1]'
		                         .format(level=LEVEL[level]))

		print('            \'journals\': [')
		for ul in uls:
			conf_tags = ul.xpath('./li/div[3][text() != "刊物全称"]/..')
			for conf_tag in conf_tags:
				conf_name = conf_tag.xpath('./div[2]/text()')[0].strip()
				conf_all_name = conf_tag.xpath('./div[3]/text()')[0].strip()
				conf_url = conf_tag.xpath('./div[5]/a/attribute::href')[0].strip()
				split_str = '/db/'
				split_index = conf_url.find(split_str)
				if split_index >= 0:
					conf_url = conf_url[split_index + len(split_str):]

				if conf_url.endswith('index.html'):
					conf_url = conf_url.strip('index.html')

				conf_url = conf_url.strip().strip('/')
				journals.append(conf_url)

				# 若没有获取到dblp的相对url地址，则标上FIXME注释
				if not (conf_url.startswith('journals/') or conf_url.startswith('conf/')):
					print('                # FIXME')

				print('                # {name} ({all_name})'.format(name=conf_name, all_name=conf_all_name))
				print('                \'{}\','.format(conf_url))
				print()

		print('            ],')
		print('        },')

	print('    ],')
	print('},')
	return journals


# ccf内所有领域
domains = [
	{
		"name": "计算机体系结构/并行与分布计算/存储系统",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/ARCH_DCP_SS"
	},
	{
		"name": "计算机网络",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/CN"
	},
	{
		"name": "网络与信息安全",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/NIS"
	},
	{
		"name": "软件工程/系统软件/程序设计语言",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/TCSE_SS_PDL"
	},
	{
		"name": "数据库/数据挖掘/内容检索",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/DM_CS"
	},
	{
		"name": "计算机科学理论",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/TCS"
	},
	{
		"name": "计算机图形学与多媒体",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/CGAndMT"
	},
	{
		"name": "人工智能",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/AI"
	},
	{
		"name": "人机交互与普适计算",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/HCIAndPC"
	},
	{
		"name": "交叉/综合/新兴",
		"url": "https://www.ccf.org.cn/Academic_Evaluation/Cross_Compre_Emerging"
	}
]

# ccf所有领域ABC三类期刊会议
# 通过get_all_journals生成的键值对列表
# 有些期刊\会议无法从dblp中获取到论文，这种注释掉暂不处理
ccf = [
	# {
	# 	'name': '计算机体系结构/并行与分布计算/存储系统',
	# 	'url': 'https://www.ccf.org.cn/Academic_Evaluation/ARCH_DCP_SS',
	# 	'levels': [
	# 		{
	# 			'level': 'A',
	# 			'journals': [
	# 				# TOCS (ACM Transactions on Computer Systems)
	# 				'journals/tocs',
	#
	# 				# TOS (ACM Transactions on Storage)
	# 				'journals/tos',
	#
	# 				# TCAD (IEEE Transactions On Computer-Aided Design Of Integrated Circuits And System)
	# 				'journals/tcad',
	#
	# 				# TC (IEEE Transactions on Computers)
	# 				'journals/tc',
	#
	# 				# TPDS (IEEE Transactions on Parallel and Distributed Systems)
	# 				'journals/tpds',
	#
	# 				# PPoPP (ACM SIGPLAN Symposium on Principles & Practice of Parallel Programming)
	# 				'conf/ppopp',
	#
	# 				# FAST (Conference on File and Storage Technologies)
	# 				'conf/fast',
	#
	# 				# DAC (Design Automation Conference)
	# 				'conf/dac',
	#
	# 				# HPCA (High-Performance Computer Architecture)
	# 				'conf/cnhpca',
	#
	# 				# MICRO (IEEE/ACM International Symposium on Microarchitecture)
	# 				'journals/micro',
	#
	# 				# SC (International Conference for High Performance Computing, Networking, Storage, and Analysis)
	# 				'conf/sc',
	#
	# 				# ASPLOS (International Conference on Architectural Support for Programming Languages and Operating Systems)
	# 				'conf/asplos',
	#
	# 				# ISCA (International Symposium on Computer Architecture)
	# 				'conf/isca',
	#
	# 				# USENIX ATC (USENIX Annul Technical Conference)
	# 				'conf/usenix',
	#
	# 			],
	# 		},
	# 		{
	# 			'level': 'B',
	# 			'journals': [
	# 				# TACO (ACM Transactions on Architecture and Code Optimization)
	# 				'journals/taco',
	#
	# 				# TAAS (ACM Transactions on Autonomous and Adaptive Systems)
	# 				'journals/taas',
	#
	# 				# TODAES (ACM Transactions on Design Automation of Electronic Systems)
	# 				'journals/todaes',
	#
	# 				# TECS (ACM Transactions on Embedded Computing Systems)
	# 				'journals/tecs',
	#
	# 				# TRETS (ACM Transactions on Reconfigurable Technology and Systems)
	# 				'journals/trets',
	#
	# 				# TVLSI (IEEE Transactions on Very Large Scale Integration (VLSI) Systems)
	# 				'journals/tvlsi',
	#
	# 				# JPDC (Journal of Parallel and Distributed Computing)
	# 				'journals/jpdc',
	#
	# 				# JSA (Journal of Systems Architecture: Embedded Software Design)
	# 				'journals/jsa',
	#
	# 				# PARCO (Parallel Computing)
	# 				'conf/parco',
	#
	# 				# FIXME 无法从dblp获取
	# 				#  (Performance Evaluation: An International Journal)
	# 				# 'http://www.journals.elsevier.com/performance-evaluation',
	#
	# 				# SOCC (ACM Symposium on Cloud Computing)
	# 				'conf/cloud',
	#
	# 				# SPAA (ACM Symposium on Parallelism in Algorithms and Architectures)
	# 				'conf/spaa',
	#
	# 				# PODC (ACM Symposium on Principles of Distributed Computing)
	# 				'conf/podc',
	#
	# 				# FPGA (ACM/SIGDA International Symposium on Field-Programmable Gate Arrays)
	# 				'conf/fpga',
	#
	# 				# CGO (Code Generation and Optimization)
	# 				'conf/cgo',
	#
	# 				# DATE (Design, Automation & Test in Europe)
	# 				'conf/date',
	#
	# 				# EuroSys (European Conference on Computer Systems)
	# 				'conf/eurosys',
	#
	# 				# FIXME 无法从dblp获取
	# 				# HOT CHIPS (ACM Symposium on High Performance Chips)
	# 				# 'http://www.hotchips.org',
	#
	# 				# CLUSTER (IEEE International Conference on Cluster Computing)
	# 				'conf/cluster',
	#
	# 				# ICCD (International Conference on Computer Design)
	# 				'conf/iccd',
	#
	# 				# ICCAD (International Conference on Computer-Aided Design)
	# 				'conf/iccad',
	#
	# 				# ICDCS (International Conference on Distributed Computing Systems)
	# 				'conf/icdcs',
	#
	# 				# CODES+ISSS (International Conference on Hardware/Software Co-design and System Synthesis)
	# 				'conf/codes',
	#
	# 				# HiPEAC (International Conference on High Performance and Embedded Architectures and Compilers)
	# 				'conf/hipeac',
	#
	# 				# SIGMETRICS (International Conference on Measurement and Modeling of Computer Systems)
	# 				'conf/sigmetrics',
	#
	# 				# PACT (International Conference on Parallel Architectures and Compilation Techniques)
	# 				'conf/IEEEpact',
	#
	# 				# ICPP (International Conference on Parallel Processing)
	# 				'conf/icpp',
	#
	# 				# ICS (International Conference on Supercomputing)
	# 				'conf/ics',
	#
	# 				# VEE (International Conference on Virtual Execution Environments)
	# 				'conf/vee',
	#
	# 				# IPDPS (International Parallel & Distributed Processing Symposium)
	# 				'conf/ipps',
	#
	# 				# Performance (International Symposium on Computer Performance, Modeling, Measurements and Evaluation)
	# 				'conf/performance',
	#
	# 				# HPDC (International Symposium on High Performance Distributed Computing)
	# 				'conf/hpdc',
	#
	# 				# ITC (International Test Conference)
	# 				'conf/itc',
	#
	# 				# LISA (Large Installation system Administration Conference)
	# 				'conf/lisa',
	#
	# 				# MSST (Mass Storage Systems and Technologies)
	# 				'conf/mss',
	#
	# 				# RTAS (Real-Time and Embedded Technology and Applications Symposium)
	# 				'conf/rtas',
	#
	# 			],
	# 		},
	# 		{
	# 			'level': 'C',
	# 			'journals': [
	# 				# JETC (ACM Journal on Emerging Technologies in Computing Systems)
	# 				'journals/jetc',
	#
	# 				#  (Concurrency and Computation: Practice and Experience)
	# 				'journals/concurrency',
	#
	# 				# DC (Distributed Computing)
	# 				'journals/dc',
	#
	# 				# FGCS (Future Generation Computer Systems)
	# 				'journals/fgcs',
	#
	# 				# TCC (IEEE Transactions on Cloud Computing)
	# 				'journals/tcc',
	#
	# 				# Integration (Integration, the VLSI Journal)
	# 				'journals/integration',
	#
	# 				# FIXME 无法从dblp获取
	# 				# JETTA (Journal of Electronic Testing-Theory and Applications)
	# 				# 'http://link.springer.com/journal/10836',
	#
	# 				# FIXME 无法从dblp获取
	# 				# JGC (The Journal of Grid computing)
	# 				# 'http://link.springer.com/journal/10723',
	#
	# 				# MICPRO (Microprocessors and Microsystems: Embedded Hardware Design)
	# 				'journals/mam',
	#
	# 				# RTS (Real-Time Systems)
	# 				'journals/rts',
	#
	# 				# TJSC (The Journal of Supercomputing)
	# 				'journals/tjs',
	#
	# 				# CF (ACM International Conference on Computing Frontiers)
	# 				'conf/cf',
	#
	# 				# SYSTOR (ACM International Systems and Storage Conference)
	# 				'conf/systor',
	#
	# 				# NOCS (ACM/IEEE International Symposium on Networks-on-Chip)
	# 				'conf/nocs',
	#
	# 				# ASAP (Application-Specific Systems, Architectures, and Processors)
	# 				'conf/asap',
	#
	# 				# ASP-DAC (Asia and South Pacific Design Automation Conference)
	# 				'conf/aspdac',
	#
	# 				# Euro-Par (European Conference on Parallel and Distributed Computing)
	# 				'conf/europar',
	#
	# 				# ETS (European Test Symposium)
	# 				'conf/ets',
	#
	# 				# FPL (Field Programmable Logic and Applications)
	# 				'conf/fpl',
	#
	# 				# FCCM (Field-Programmable Custom Computing Machines)
	# 				'conf/fccm',
	#
	# 				# GLSVLSI (Great Lakes Symposium on VLSI)
	# 				'conf/glvlsi',
	#
	# 				# ATS (IEEE Asian Test Symposium)
	# 				'conf/ats',
	#
	# 				# HPCC (IEEE International Conference on High Performance Computing and Communications)
	# 				'conf/hpcc',
	#
	# 				# HiPC (IEEE International Conference on High Performance Computing, Data and Analytics)
	# 				'conf/hipc',
	#
	# 				# MASCOTS (IEEE International Symposium on Modeling, Analysis, and Simulation of Computer and Telecommunication Systems)
	# 				'conf/mascots',
	#
	# 				# ISPA (IEEE International Symposium on Parallel and Distributed Processing with Applications)
	# 				'conf/ispa',
	#
	# 				# CCGRID (IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing)
	# 				'conf/ccgrid',
	#
	# 				# NPC (IFIP International Conference on Network and Parallel Computing)
	# 				'conf/npc',
	#
	# 				# ICA3PP (International Conference on Algorithms and Architectures for Parallel Processing)
	# 				'conf/ica3pp',
	#
	# 				# CASES (International Conference on Compilers, Architectures, and Synthesis for Embedded Systems)
	# 				'conf/cases',
	#
	# 				# FPT (International Conference on Field-Programmable Technology)
	# 				'conf/fpt',
	#
	# 				# ICPADS (International Conference on Parallel and Distributed Systems)
	# 				'conf/icpads',
	#
	# 				# ISCAS (International Symposium on Circuits and Systems)
	# 				'conf/iscas',
	#
	# 				# ISLPED (International Symposium on Low Power Electronics and Design)
	# 				'conf/islped',
	#
	# 				# ISPD (International Symposium on Physical Design)
	# 				'conf/ispd',
	#
	# 				# HotI (Symposium on High-Performance Interconnects)
	# 				'conf/hoti',
	#
	# 				# VTS (VLSI Test Symposium)
	# 				'conf/vts',
	#
	# 			],
	# 		},
	# 	],
	# },
	# {
	# 	'name': '计算机网络',
	# 	'url': 'https://www.ccf.org.cn/Academic_Evaluation/CN',
	# 	'levels': [
	# 		{
	# 			'level': 'A',
	# 			'journals': [
	# 				# JSAC (IEEE Journal on Selected Areas in Communications)
	# 				'journals/jsac',

	# 				# TMC (IEEE Transactions on Mobile Computing)
	# 				'journals/tmc',

	# 				# TON (IEEE/ACM Transactions on Networking)
	# 				'journals/ton',

	# 				# SIGCOMM (ACM International Conference on Applications, Technologies, Architectures, and Protocols for Computer Communication)
	# 				'conf/sigcomm',

	# 				# MobiCom (ACM International Conference on Mobile Computing and Networking)
	# 				'conf/mobicom',

	# 				# INFOCOM (IEEE International Conference on Computer Communications)
	# 				'conf/infocom',

	# 				# NSDI (Symposium on Network System Design and Implementation)
	# 				'conf/nsdi',

	# 			],
	# 		},
	# 		{
	# 			'level': 'B',
	# 			'journals': [
	# 				# TOIT (ACM Transactions on Internet Technology)
	# 				'journals/toit',

	# 				# TOMCCAP (ACM Transactions on Multimedia Computing, Communications and Applications)
	# 				'journals/tomccap',

	# 				# TOSN (ACM Transactions on Sensor Networks)
	# 				'journals/tosn',

	# 				# CN (Computer Networks)
	# 				'journals/cn',

	# 				# TCOM (IEEE Transactions on Communications)
	# 				'journals/tcom',

	# 				# TWC (IEEE Transactions on Wireless Communications)
	# 				'journals/twc',

	# 				# SenSys (ACM Conference on Embedded Networked Sensor Systems)
	# 				'conf/sensys',

	# 				# CoNEXT (ACM International Conference on emerging Networking EXperiments and Technologies)
	# 				'conf/conext',

	# 				# SECON (IEEE Communications Society Conference on Sensor and Ad Hoc Communications and Networks)
	# 				'conf/secon',

	# 				# IPSN (International Conference on Information Processing in Sensor Networks)
	# 				'conf/ipsn',

	# 				# MobiSys (International Conference on Mobile Systems, Applications, and Services)
	# 				'conf/mobisys',

	# 				# ICNP (International Conference on Network Protocols)
	# 				'conf/icnp',

	# 				# MobiHoc (International Symposium on Mobile Ad Hoc Networking and Computing)
	# 				'conf/mobihoc',

	# 				# NOSSDAV (International Workshop on Network and Operating System Support for Digital Audio and Video)
	# 				'conf/nossdav',

	# 				# IWQoS (International Workshop on Quality of Service)
	# 				'conf/iwqos',

	# 				# IMC (Internet Measurement Conference)
	# 				'conf/imc',

	# 			],
	# 		},
	# 		{
	# 			'level': 'C',
	# 			'journals': [
	# 				#  (Ad hoc Networks)
	# 				'journals/adhoc',

	# 				# CC (Computer Communications)
	# 				'journals/comcom',

	# 				# TNSM (IEEE Transactions on Network and Service Management)
	# 				'journals/tnsm',

	# 				#  (IET Communications)
	# 				'journals/iet-com',

	# 				# JNCA (Journal of Network and Computer Applications)
	# 				'journals/jnca',

	# 				# MONET (Mobile Networks & Applications)
	# 				'journals/monet',

	# 				#  (Networks)
	# 				'journals/networks',

	# 				# PPNA (Peer-to-Peer Networking and Applications)
	# 				'journals/ppna',

	# 				# WCMC (Wireless Communications & Mobile Computing)
	# 				'journals/wicomm',

	# 				#  (Wireless Networks)
	# 				'journals/winet',

	# 				# ANCS (Architectures for Networking and Communications Systems)
	# 				'conf/ancs',

	# 				# APNOMS (Asia-Pacific Network Operations and Management Symposium)
	# 				'conf/apnoms',

	# 				# FORTE (Formal Techniques for Networked and Distributed Systems)
	# 				'conf/forte',

	# 				# LCN (IEEE Conference on Local Computer Networks)
	# 				'conf/lcn',

	# 				# GLOBECOM (IEEE Global Communications Conference)
	# 				'conf/globecom',

	# 				# ICC (IEEE International Conference on Communications)
	# 				'conf/icc',

	# 				# ICCCN (IEEE International Conference on Computer Communications and Networks)
	# 				'conf/icccn',

	# 				# MASS (IEEE International Conference on Mobile Ad-hoc and Sensor Systems)
	# 				'conf/mass',

	# 				# P2P (IEEE International Conference on P2P Computing)
	# 				'conf/p2p',

	# 				# IPCCC (IEEE International Performance Computing and Communications Conference)
	# 				'conf/ipccc',

	# 				# WoWMoM (IEEE International Symposium on a World of Wireless Mobile and Multimedia Networks)
	# 				'conf/wowmom',

	# 				# ISCC (IEEE Symposium on Computers and Communications)
	# 				'conf/iscc',

	# 				# WCNC (IEEE Wireless Communications & Networking Conference)
	# 				'conf/wcnc',

	# 				# Networking (IFIP International Conferences on Networking)
	# 				'conf/networking',

	# 				# IM (IFIP/IEEE International Symposium on Integrated Network Management)
	# 				'conf/im',

	# 				# MSN (International Conference on Mobile Ad-hoc and Sensor Networks)
	# 				'conf/msn',

	# 				# MSWiM (International Conference on Modeling, Analysis and Simulation of Wireless and Mobile Systems)
	# 				'conf/mswim',

	# 				# WASA (International Conference on Wireless Algorithms, Systems, and Applications)
	# 				'conf/wasa',

	# 				# HotNets (The Workshop on Hot Topics in Networks)
	# 				'conf/hotnets',

	# 			],
	# 		},
	# 	],
	# },
	# {
	# 	'name': '网络与信息安全',
	# 	'url': 'https://www.ccf.org.cn/Academic_Evaluation/NIS',
	# 	'levels': [
	# 		{
	# 			'level': 'A',
	# 			'journals': [
	# 				# TDSC (IEEE Transactions on Dependable and Secure Computing)
	# 				'journals/tdsc',

	# 				# TIFS (IEEE Transactions on Information Forensics and Security)
	# 				'journals/tifs',

	# 				#  (Journal of Cryptology)
	# 				'journals/joc',

	# 				# CCS (ACM Conference on Computer and Communications Security)
	# 				'conf/ccs',

	# 				# EUROCRYPT (European Cryptology Conference)
	# 				'conf/eurocrypt',

	# 				# S&P (IEEE Symposium on Security and Privacy)
	# 				'conf/sp',

	# 				# CRYPTO (International Cryptology Conference)
	# 				'conf/crypto',

	# 				# USENIX Security (Usenix Security Symposium)
	# 				'conf/uss',

	# 			],
	# 		},
	# 		{
	# 			'level': 'B',
	# 			'journals': [
	# 				# FIXME TOPS前身是TISSEC
	# 				# TOPS (ACM Transactions on Privacy and Security)
	# 				'journals/tissec',

	# 				#  (Computers & Security)
	# 				'journals/compsec',

	# 				#  (Designs, Codes and Cryptography)
	# 				'journals/dcc',

	# 				# JCS (Journal of Computer Security)
	# 				'journals/jcs',

	# 				# ACSAC (Annual Computer Security Applications Conference)
	# 				'conf/acsac',

	# 				# ASIACRYPT (Annual International Conference on the Theory and Application of Cryptology and Information Security)
	# 				'conf/asiacrypt',

	# 				# ESORICS (European Symposium on Research in Computer Security)
	# 				'conf/esorics',

	# 				# FSE (Fast Software Encryption)
	# 				'conf/fse',

	# 				# CSFW (IEEE Computer Security Foundations Workshop)
	# 				'conf/csfw',

	# 				# SRDS (IEEE International Symposium on Reliable Distributed Systems)
	# 				'conf/srds',

	# 				# CHES (International Conference on Cryptographic Hardware and Embedded Systems)
	# 				'conf/ches',

	# 				# DSN (International Conference on Dependable Systems and Networks)
	# 				'conf/dsn',

	# 				# RAID (International Symposium on Recent Advances in Intrusion Detection)
	# 				'conf/raid',

	# 				# PKC (International Workshop on Practice and Theory in Public Key Cryptography)
	# 				'conf/pkc',

	# 				# NDSS (ISOC Network and Distributed System Security Symposium)
	# 				'conf/ndss',

	# 				# TCC (Theory of Cryptography Conference)
	# 				'conf/tcc',

	# 			],
	# 		},
	# 		{
	# 			'level': 'C',
	# 			'journals': [
	# 				# FIXME 无法从dblp获取
	# 				# CLSR (Computer Law and Security Review)
	# 				# 'http://www.journals.elsevier.com/computer-law-and-security-review',

	# 				#  (EURASIP Journal on Information Security)
	# 				'journals/ejisec',

	# 				#  (IET Information Security)
	# 				'journals/iet-ifs',

	# 				# IMCS (Information Management & Computer Security)
	# 				'journals/imcs',

	# 				# IJICS (International Journal of Information and Computer Security)
	# 				'journals/ijics',

	# 				# IJISP (International Journal of Information Security and Privacy)
	# 				'journals/ijisp',

	# 				# JISA (Journal of Information Security and Application)
	# 				'journals/istr',

	# 				# SCN (Security and Communication Networks)
	# 				'journals/scn',

	# 				# WiSec (ACM Conference on Security and Privacy in Wireless and Mobile Networks)
	# 				'conf/wisec',

	# 				# SACMAT (ACM Symposium on Access Control Models and Technologies)
	# 				'conf/sacmat',

	# 				# DRM (ACM Workshop on Digital Rights Management)
	# 				'conf/drm',

	# 				# IH&MMSec (ACM Workshop on Information Hiding and Multimedia Security)
	# 				'conf/ih',

	# 				# ACNS (Applied Cryptography and Network Security)
	# 				'conf/acns',

	# 				# FIXME 改成asiaccs
	# 				# AsiaCCS (Asia Conference on Computer and Communications Security)
	# 				'conf/asiaccs',

	# 				# ACISP (AustralasiaConferenceonInformation SecurityandPrivacy)
	# 				'conf/acisp',

	# 				# CT-RSA (RSA Conference, Cryptographers' Track)
	# 				'conf/ctrsa',

	# 				# DIMVA (Detection of Intrusions and Malware &Vulnerability Assessment)
	# 				'conf/dimva',

	# 				# DFRWS (Digital Forensic Research Workshop)
	# 				'conf/dfrws',

	# 				# FC (Financial Cryptography and Data Security)
	# 				'conf/fc',

	# 				# TrustCom (IEEE International Conference on Trust,Security and Privacy in Computing and Communications)
	# 				'conf/trustcom',

	# 				# SEC (IFIP International Information Security Conference)
	# 				'conf/sec',

	# 				# FIXME 无法从dblp无法获取
	# 				# IFIP WG 11.9 (IFIP WG 11.9 International Conference on Digital Forensics)
	# 				# 'http://www.ifip119.org/Conferences',

	# 				# ISC (Information Security Conference)
	# 				'conf/isw',

	# 				# ICDF2C (International Conference on Digital Forensics & Cyber Crime)
	# 				'conf/icdf2c',

	# 				# ICICS (International Conference on Information and Communications Security)
	# 				'conf/icics',

	# 				# SecureComm (International Conference on Security and Privacy in Communication Networks)
	# 				'conf/securecomm',

	# 				# NSPW (New Security Paradigms Workshop)
	# 				'conf/nspw',

	# 				# PAM (Passive and Active Measurement Conference)
	# 				'conf/pam',

	# 				# PETS (Privacy Enhancing Technologies Symposium)
	# 				'conf/pet',

	# 				# SAC (Selected Areas in Cryptography)
	# 				'conf/sacrypt',

	# 				# SOUPS (Symposium On Usable Privacy and Security)
	# 				'conf/soups',

	# 				# FIXME 无法从dblp获取
	# 				# HotSec (USENIX Workshop on Hot Topics in Security)
	# 				# 'http://www.usenix.org/events',

	# 			],
	# 		},
	# 	],
	# },
	{
		'name': '软件工程/系统软件/程序设计语言',
		'url': 'https://www.ccf.org.cn/Academic_Evaluation/TCSE_SS_PDL',
		'levels': [
			{
				'level': 'A',
				'journals': [
					# TOPLAS (ACM Transactions on Programming Languages & Systems)
					'journals/toplas',

					# TOSEM (ACM Transactions on Software Engineering and Methodology)
					'journals/tosem',

					# TSE (IEEE Transactions on Software Engineering)
					'journals/tse',

					# PLDI (ACM SIGPLAN Symposium on Programming Language Design & Implementation)
					'conf/pldi',

					# POPL (ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages)
					'conf/popl',

					# FSE/ESEC (ACM SIGSOFT Symposium on the Foundation of Software Engineering/ European Software Engineering Conference)
					'conf/sigsoft',

					# SOSP (ACM Symposium on Operating Systems Principles)
					'conf/sosp',

					# OOPSLA (Conference on Object-Oriented Programming Systems, Languages,and Applications)
					'conf/oopsla',

					# ASE (International Conference on Automated Software Engineering)
					'conf/kbse',

					# ICSE (International Conference on Software Engineering)
					'conf/icse',

					# ISSTA (International Symposium on Software Testing and Analysis)
					'conf/issta',

					# OSDI (USENIX Symposium on Operating Systems Design and Implementations)
					'conf/osdi',

				],
			},
			{
				'level': 'B',
				'journals': [
					# ASE (Automated Software Engineering)
					'journals/ase',

					# ESE (Empirical Software Engineering)
					'journals/ese',

					# TSC (IEEE Transactions on Service Computing)
					'journals/tsc',

					# IETS (IET Software)
					'journals/iee',

					# IST (Information and Software Technology)
					'journals/infsof',

					# JFP (Journal of Functional Programming)
					'journals/jfp',

					#  (Journal of Software: Evolution and Process)
					'journals/smr',

					# JSS (Journal of Systems and Software)
					'journals/jss',

					# RE (Requirements Engineering)
					'journals/re',

					# SCP (Science of Computer Programming)
					'journals/scp',

					# SoSyM (Software and System Modeling)
					'journals/sosym',

					# STVR (Software Testing, Verification and Reliability)
					'journals/stvr',

					# SPE (Software: Practice and Experience)
					'journals/spe',

					# ECOOP (European Conference on Object-Oriented Programming)
					'conf/ecoop',

					# FIXME ETAPS是CAAP，CC，ESOP和TAPSOFT的后续会议。
					# ETAPS (European Joint Conferences on Theory and Practice of Software)
					# 'conf/etaps',
					'conf/caap',
					'conf/cc',
					'conf/esop',
					'conf/tapsoft',

					# ICPC (IEEE International Conference on Program Comprehension)
					'conf/iwpc',

					# RE (IEEE International Requirement Engineering Conference)
					'conf/re',

					# CAiSE (International Conference on Advanced Information Systems Engineering)
					'conf/caise',

					# ICFP (International Conference on Function Programming)
					'conf/icfp',

					# LCTES (International Conference on Languages,Compilers, Tools and Theory for Embedded Systems)
					'conf/lctrts',

					# MoDELS (International Conference on Model Driven Engineering Languages and Systems)
					'conf/models',

					# CP (International Conference on Principles and Practice of Constraint Programming)
					'conf/cp',

					# ICSOC (International Conference on Service Oriented Computing)
					'conf/icsoc',

					# SANER (International Conference on Software Analysis, Evolution, and Reengineering)
					'conf/wcre',

					# ICSME (International Conference on Software Maintenance and Evolution)
					'conf/icsm',

					# VMCAI (International Conference on Verification,Model Checking, and Abstract Interpretation)
					'conf/vmcai',

					# ICWS (International Conference on Web Services（Research Track）)
					'conf/icws',

					# Middleware (International Middleware Conference)
					'conf/middleware',

					# SAS (International Static Analysis Symposium)
					'conf/sas',

					# ESEM (International Symposium on Empirical Software Engineering and Measurement)
					'conf/esem',

					# FM (International Symposium on Formal Methods)
					'conf/fm',

					# ISSRE (International Symposium on Software Reliability Engineering)
					'conf/issre',

					# HotOS (USENIX Workshop on Hot Topics in Operating Systems)
					'conf/hotos',

				],
			},
			{
				'level': 'C',
				'journals': [
					# CL (Computer Languages, Systems and Structures)
					'journals/cl',

					# IJSEKE (International Journal on Software Engineering and Knowledge Engineering)
					'journals/ijseke',

					# STTT (International Journal on Software Tools for Technology Transfer)
					'journals/sttt',

					# FIXME 去掉jlap.html
					# JLAP (Journal of Logic and Algebraic Programming)
					'journals/jlp',

					# JWE (Journal of Web Engineering)
					'journals/jwe',

					# SOCA (Service Oriented Computing and Applications)
					'journals/soca',

					# SQJ (Software Quality Journal)
					'journals/sqj',

					# TPLP (Theory and Practice of Logic Programming)
					'journals/tplp',

					# PEPM (ACM SIGPLAN Workshop on Partial Evaluation and Program Manipulation)
					'conf/pepm',

					# PASTE (ACMSIGPLAN-SIGSOFT Workshop on Program Analysis for Software Tools and Engineering)
					'conf/paste',

					# APLAS (Asian Symposium on Programming Languages and Systems)
					'conf/aplas',

					# APSEC (Asia-Pacific Software Engineering Conference)
					'conf/apsec',

					# EASE (Evaluation and Assessment in Software Engineering)
					'conf/ease',

					# ICECCS (IEEE International Conference on Engineering of Complex Computer Systems)
					'conf/iceccs',

					# ICST (IEEE International Conference on Software Testing, Verification and Validation)
					'conf/icst',

					# ISPASS (IEEE International Symposium on Performance Analysis of Systems and Software)
					'conf/ispass',

					# SCAM (IEEE International Working Conference on Source Code Analysis and Manipulation)
					'conf/scam',

					# COMPSAC (International Computer Software and Applications Conference)
					'conf/compsac',

					# ICFEM (International Conference on Formal Engineering Methods)
					'conf/icfem',

					# TOOLS (International Conference on Objects, Models, Components, Patterns)
					'conf/tools',

					# SCC (International Conference on Service Computing)
					'conf/IEEEscc',

					# ICSSP (International Conference on Software and System Process)
					'conf/ispw',

					# SEKE (International Conference on Software Engineering and Knowledge Engineering)
					'conf/seke',

					# QRS (International Conference on Software Quality, Reliability and Security)
					'conf/qrs',

					# ICSR (International Conference on Software Reuse)
					'conf/icsr',

					# ICWE (International Conference on Web Engineering)
					'conf/icwe',

					# SPIN (International SPIN Workshop on Model Checking of Software)
					'conf/spin',

					# ATVA (International Symposium on Automated Technology for Verification and Analysis)
					'conf/atva',

					# LOPSTR (International Symposium on Logic-based Program Synthesis and Transformation)
					'conf/lopstr',

					# TASE (International Symposium on Theoretical Aspects of Software Engineering)
					'conf/tase',

					# MSR (Mining Software Repositories)
					'conf/msr',

					# REFSQ (Requirements Engineering: Foundation for Software Quality)
					'conf/refsq',

					# WICSA (Working IEEE/IFIP Conference on Software Architecture)
					'conf/wicsa',

				],
			},
		],
	},
	{
		'name': '数据库/数据挖掘/内容检索',
		'url': 'https://www.ccf.org.cn/Academic_Evaluation/DM_CS',
		'levels': [
			{
				'level': 'A',
				'journals': [
					# TODS (ACM Transactions on Database Systems)
					'journals/tods',

					# TOIS (ACM Transactions on Information Systems)
					'journals/tois',

					# TKDE (IEEE Transactions on Knowledge and Data Engineering)
					'journals/tkde',

					# VLDBJ (The VLDB Journal)
					'journals/vldb',

					# SIGMOD (ACM Conference on Management of Data)
					'conf/sigmod',

					# SIGKDD (ACM Knowledge Discovery and Data Mining)
					'conf/kdd',

					# ICDE (IEEE International Conference on Data Engineering)
					'conf/icde',

					# SIGIR (International Conference on Research on Development in Information Retrieval)
					'conf/sigir',

					# VLDB (International Conference on Very Large Data Bases)
					'conf/vldb',

				],
			},
			{
				'level': 'B',
				'journals': [
					# TKDD (ACM Transactions on Knowledge  Discovery from Data)
					'journals/tkdd',

					# TWEB (ACM Transactions on the Web)
					'journals/tweb',

					# AEI (Advanced Engineering Informatics)
					'journals/aei',

					# DKE (Data and Knowledge Engineering)
					'journals/dke',

					# DMKD (Data Mining and Knowledge  Discovery)
					'journals/datamine',

					# EJIS (European Journal of Information Systems)
					'journals/ejis',

					#  (GeoInformatica)
					'journals/geoinformatica',

					# IPM (Information Processing and Management)
					'journals/ipm',

					#  (Information Sciences)
					'journals/isci',

					# IS (Information Systems)
					'journals/is',

					# JASIST (Journal of the American Society for Information Science and Technology)
					'journals/jasis',

					# JWS (Journal of Web Semantics)
					'journals/ws',

					# KAIS (Knowledge and Information Systems)
					'journals/kais',

					# CIKM (ACM International Conference on Information and Knowledge Management)
					'conf/cikm',

					# WSDM (ACM International Conference on Web Search and Data Mining)
					'conf/wsdm',

					# PODS (ACM Symposium on Principles of Database Systems)
					'conf/pods',

					# DASFAA (Database Systems for Advanced Applications)
					'conf/dasfaa',

					# ECML-PKDD (European Conference on Machine Learning and Principles and Practice of Knowledge Discovery in Databases)
					'conf/ecml',

					# ISWC (IEEE International Semantic Web Conference)
					'conf/semweb',

					# ICDM (International Conference on Data Mining)
					'conf/icdm',

					# ICDT (International Conference on Database Theory)
					'conf/icdt',

					# EDBT (International Conference on Extending DB Technology)
					'conf/edbt',

					# CIDR (International Conference on Innovative Data Systems Research)
					'conf/cidr',

					# SDM (SIAM International Conference on Data Mining)
					'conf/sdm',

				],
			},
			{
				'level': 'C',
				'journals': [
					# DPD (Distributed and Parallel Databases)
					'journals/dpd',

					# I&M (Information and Management)
					'journals/iam',

					# IPL (Information Processing Letters)
					'journals/ipl',

					# IR (Information Retrieval Journal)
					'journals/ir',

					# IJCIS (International Journal of Cooperative Information Systems)
					'journals/ijcis',

					# IJGIS (International Journal of Geographical Information Science)
					'journals/gis',

					# IJIS (International Journal of Intelligent Systems)
					'journals/ijis',

					# IJKM (International Journal of Knowledge Management)
					'journals/ijkm',

					# IJSWIS (International Journal on Semantic Web and Information Systems)
					'journals/ijswis',

					# JCIS (Journal of Computer Information Systems)
					'journals/jcis',

					# JDM (Journal of Database Management)
					'journals/jdm',

					# FIXME 无法从dblp获取
					# JGITM (Journal of Global Information Technology Management)
					# 'http://www.tandfonline.com/loi/ugit20#.Vnv35pN97rI',

					# JIIS (Journal of Intelligent Information Systems)
					'journals/jiis',

					# JSIS (Journal of Strategic Information Systems)
					'journals/jsis',

					# APWeb (Asia Pacific Web Conference)
					'conf/apweb',

					# DEXA (Database and Expert System Applications)
					'conf/dexa',

					# ECIR (European Conference on IR Research)
					'conf/ecir',

					# ESWC (Extended Semantic Web Conference)
					'conf/esws',

					# WebDB (International ACM Workshop on Web and Databases)
					'conf/webdb',

					# ER (International Conference on Conceptual Modeling)
					'conf/er',

					# MDM (International Conference on Mobile Data Management)
					'conf/mdm',

					# SSDBM (International Conference on Scientific and Statistical DB Management)
					'conf/ssdbm',

					# WAIM (International Conference on Web Age Information Management)
					'conf/waim',

					# SSTD (International Symposium on Spatial and Temporal Databases)
					'conf/ssd',

					# PAKDD (Pacific-Asia Conference on Knowledge Discovery and Data Mining)
					'conf/pakdd',

					# WISE (Web Information Systems Engineering)
					'conf/wise',

				],
			},
		],
	},
	{
		'name': '计算机科学理论',
		'url': 'https://www.ccf.org.cn/Academic_Evaluation/TCS',
		'levels': [
			{
				'level': 'A',
				'journals': [
					# TIT (IEEE Transactions on Information Theory)
					'journals/tit',

					# IANDC (Information and Computation)
					'journals/iandc',

					# SICOMP (SIAM Journal on Computing)
					'journals/siamcomp',

					# STOC (ACM Symposium on Theory of Computing)
					'conf/stoc',

					# SODA (ACM-SIAM Symposium on Discrete Algorithms)
					'conf/soda',

					# CAV (Computer Aided Verification)
					'conf/cav',

					# FOCS (IEEE Annual Symposium on Foundations of Computer Science)
					'conf/focs',

					# LICS (IEEE Symposium on Logic in Computer Science)
					'conf/lics',

				],
			},
			{
				'level': 'B',
				'journals': [
					# TALG (ACM Transactions on Algorithms)
					'journals/talg',

					# TOCL (ACM Transactions on Computational Logic)
					'journals/tocl',

					# TOMS (ACM Transactions on Mathematical Software)
					'journals/toms',

					# Algorithmica (Algorithmica)
					'journals/algorithmica',

					# CC (Computational complexity)
					'journals/cc',

					# FAC (Formal Aspects of Computing)
					'journals/fac',

					# FMSD (Formal Methods in System Design)
					'journals/fmsd',

					# INFORMS (INFORMS Journal on Computing)
					'journals/informs',

					# JCSS (Journal of Computer and System Sciences)
					'journals/jcss',

					# JGO (Journal of Global Optimization)
					'journals/jgo',

					# JSC (Journal of Symbolic Computation)
					'journals/jsc',

					# MSCS (Mathematical Structures in Computer Science)
					'journals/mscs',

					# TCS (Theoretical Computer Science)
					'journals/tcs',

					# SoCG (ACM Symposium on Computational Geometry)
					'conf/compgeom',

					# ESA (European Symposium on Algorithms)
					'conf/esa',

					# CCC (IEEE Conference on Computational Complexity)
					'conf/coco',

					# ICALP (International Colloquium on Automata, Languages and Programming)
					'conf/icalp',

					# CADE/IJCAR (International Conference on Automated Deduction/International Joint Conference on Automated Reasoning)
					'conf/cade',

					# CONCUR (International Conference on Concurrency Theory)
					'conf/concur',

					# HSCC (International Conference on Hybrid Systems: Computation and Control)
					'conf/hybrid',

					# SAT (Theory and Applications of Satisfiability Testing)
					'conf/sat',

				],
			},
			{
				'level': 'C',
				'journals': [
					# ACTA (Acta Informatica)
					'journals/acta',

					# APAL (Annals of Pure and Applied Logic)
					'journals/apal',

					# DAM (Discrete Applied Mathematics)
					'journals/dam',

					# FUIN (Fundamenta Informaticae)
					'journals/fuin',

					# LISP (Higher-Order and Symbolic Computation)
					'journals/lisp',

					# FIXME 在数据库中出现过
					# IPL (Information Processing Letters)
					'journals/ipl',

					# JCOMPLEXITY (Journal of Complexity)
					'journals/jc',

					# LOGCOM (Journal of Logic and Computation)
					'journals/logcom',

					# JSL (Journal of Symbolic Logic)
					'journals/jsyml',

					# LMCS (Logical Methods in Computer Science)
					'journals/lmcs',

					# SIDMA (SIAM Journal on Discrete Mathematics)
					'journals/siamdm',

					#  (Theory of Computing Systems)
					'journals/mst',

					# CSL (Computer Science Logic)
					'conf/csl',

					# FMCAD (Formal Method in Computer-Aided Design)
					'conf/fmcad',

					# FSTTCS (Foundations of Software Technology and Theoretical Computer Science)
					'conf/fsttcs',

					# DSAA (IEEE International Conference on Data Science and Advanced Analytics)
					'conf/dsaa',

					# ICTAC (International Colloquium on Theoretical Aspects of Computing)
					'conf/ictac',

					# IPCO (International Conference on Integer Programming and Combinatorial Optimization)
					'conf/ipco',

					# RTA (International Conference on Rewriting Techniques and Applications)
					'conf/rta',

					# ISAAC (International Symposium on Algorithms and Computation)
					'conf/isaac',

					# MFCS (Mathematical Foundations of Computer Science)
					'conf/mfcs',

					# STACS (Symposium on Theoretical Aspects of Computer Science)
					'conf/stacs',

				],
			},
		],
	},
	{
		'name': '计算机图形学与多媒体',
		'url': 'https://www.ccf.org.cn/Academic_Evaluation/CGAndMT',
		'levels': [
			{
				'level': 'A',
				'journals': [
					# TOG (ACM Transactions on Graphics)
					'journals/tog',

					# TIP (IEEE Transactions on Image Processing)
					'journals/tip',

					# TVCG (IEEE Transactions on Visualization and Computer Graphics)
					'journals/tvcg',

					# ACM MM (ACM International Conference on Multimedia)
					'conf/mm',

					# SIGGRAPH (ACM SIGGRAPH Annual Conference)
					'conf/siggraph',

					# VR (IEEE Virtual Reality)
					'conf/vr',

					# IEEE VIS (IEEE Visualization Conference)
					'conf/visualization',

				],
			},
			{
				'level': 'B',
				'journals': [
					# FIXME 在计算机网络中已出现
					# TOMCCAP (ACM Transactions on Multimedia Computing,Communications and Application)
					'journals/tomccap',

					# CAGD (Computer Aided Geometric Design)
					'journals/cagd',

					# CGF (Computer Graphics Forum)
					'journals/cgf',

					# CAD (Computer-Aided Design)
					'journals/cad',

					# GM (Graphical Models)
					'journals/cvgip',

					# TCSVT (IEEE Transactions on Circuits and Systems for Video Technology)
					'journals/tcsv',

					# TMM (IEEE Transactions on Multimedia)
					'journals/tmm',

					# FIXME 无法从dblp获取
					# JASA (Journal of The Acoustical Society of America)
					# 'http://scitation.aip.org/content/asa/journal/jasa',

					# SIIMS (SIAM Journal on Imaging Sciences)
					'journals/siamis',

					# Speech Com (Speech Communication)
					'journals/speech',

					# ICMR (ACM SIGMM International Conference on Multimedia Retrieval)
					'conf/mir',

					# SI3D (ACM Symposium on Interactive 3D Graphics)
					'conf/si3d',

					# SCA (ACM/Eurographics Symposium on Computer Animation)
					'conf/sca',

					# DCC (Data Compression Conference)
					'conf/dcc',

					# FIXME 文章发在cgf(Computer Graphics Forum)？
					# EG (Eurographics)
					'conf/eurographics',

					# EuroVis (Eurographics Conference on Visualization)
					'conf/vissym',

					# SGP (Eurographics Symposium on Geometry Processing)
					'conf/sgp',

					# EGSR (Eurographics Symposium on Rendering)
					'conf/rt',

					# ICASSP (IEEE International Conference on Acoustics,Speech and SP)
					'conf/icassp',

					# ICME (IEEE International Conference on Multimedia& Expo)
					'conf/icmcs',

					# ISMAR (International Symposium on Mixed and Augmented Reality)
					'conf/ismar',

					# PG (Pacific Graphics: The Pacific Conference on Computer Graphics and Applications)
					'conf/pg',

					# SPM (Symposium on Solid and Physical Modeling)
					'conf/sma',

				],
			},
			{
				'level': 'C',
				'journals': [
					# CGTA (Computational Geometry: Theory and Applications)
					'journals/comgeo',

					# FIXME 又名Journal of Visualization and Computer Animation
					# CAVW (Computer Animation and Virtual Worlds)
					'journals/jvca',

					# C&G (Computers & Graphics)
					'journals/cg',

					# DCG (Discrete & Computational Geometry)
					'journals/dcg',

					# SPL (IEEE Signal Processing Letters)
					'journals/spl',

					# IET-IPR (IET Image Processing)
					'journals/iet-ipr',

					# JVCIR (Journal of Visual Communication and Image Representation)
					'journals/jvcir',

					# MS (Multimedia Systems)
					'journals/mms',

					# MTA (Multimedia Tools and Applications)
					'journals/mta',

					#  (Signal Processing)
					'journals/sigpro',

					# SPIC (Signal processing : image communication)
					'journals/spic',

					# TVC (The Visual Computer)
					'journals/vc',

					#  (ACM Symposium on Virtual Reality Software and Technology)
					'conf/vrst',

					# CASA (Computer Animation and Social Agents)
					'conf/ca',

					# CGI (Computer Graphics International)
					'conf/cgi',

					# INTERSPEECH (Conference of the International Speech Communication Association)
					'conf/interspeech',

					# GMP (Geometric Modeling and Processing)
					'conf/gmp',

					# PacificVis (IEEE Pacific Visualization Symposium)
					'conf/apvis',

					# 3DV (International Conference on 3D Vision)
					'conf/3dim',

					# CAD/Graphics (International Conference on Computer-Aided Design and Computer Graphics)
					'conf/cadgraphics',

					# ICIP (International Conference on Image Processing)
					'conf/icip',

					# MMM (International Conference on Multimedia Modeling)
					'conf/mmm',

					# PCM (Pacific-Rim Conference on Multimedia)
					'conf/pcm',

					# SMI (Shape Modeling International)
					'conf/smi',

				],
			},
		],
	},
	# {
	# 	'name': '人工智能',
	# 	'url': 'https://www.ccf.org.cn/Academic_Evaluation/AI',
	# 	'levels': [
	# 		{
	# 			'level': 'A',
	# 			'journals': [
	# 				# AI (Artificial Intelligence)
	# 				'journals/ai',
	#
	# 				# TPAMI (IEEE Trans on Pattern Analysis and Machine Intelligence)
	# 				'journals/pami',
	#
	# 				# IJCV (International Journal of Computer Vision)
	# 				'journals/ijcv',
	#
	# 				# JMLR (Journal of Machine Learning Research)
	# 				'journals/jmlr',
	#
	# 				# AAAI (AAAI Conference on Artificial Intelligence)
	# 				'conf/aaai',
	#
	# 				# NeurIPS (Annual Conference on Neural Information Processing Systems)
	# 				'conf/nips',
	#
	# 				# ACL (Annual Meeting of the Association for Computational Linguistics)
	# 				'conf/acl',
	#
	# 				# CVPR (IEEE Conference on Computer Vision and Pattern Recognition)
	# 				'conf/cvpr',
	#
	# 				# ICCV (International Conference on Computer Vision)
	# 				'conf/iccv',
	#
	# 				# ICML (International Conference on Machine Learning)
	# 				'conf/icml',
	#
	# 				# IJCAI (International Joint Conference on Artificial Intelligence)
	# 				'conf/ijcai',
	#
	# 			],
	# 		},
	# 		{
	# 			'level': 'B',
	# 			'journals': [
	# 				# TAP (ACM Transactions on Applied Perception)
	# 				'journals/tap',
	#
	# 				# TSLP (ACM Transactions on Speech and Language Processing)
	# 				'journals/tslp',
	#
	# 				# AAMAS (Autonomous Agents and Multi-Agent Systems)
	# 				'journals/aamas',
	#
	# 				#  (Computational Linguistics)
	# 				'journals/coling',
	#
	# 				# CVIU (Computer Vision and Image Understanding)
	# 				'journals/cviu',
	#
	# 				# FIXME 数据库出现过
	# 				# DKE (Data and Knowledge Engineering)
	# 				'journals/dke',
	#
	# 				#  (Evolutionary Computation)
	# 				'journals/ec',
	#
	# 				# TAC (IEEE Transactions on Affective Computing)
	# 				'journals/taffco',
	#
	# 				# TASLP (IEEE Transactions on Audio, Speech, and Language Processing)
	# 				'journals/taslp',
	#
	# 				#  (IEEE Transactions on Cybernetics)
	# 				'journals/tcyb',
	#
	# 				# TEC (IEEE Transactions on Evolutionary Computation)
	# 				'journals/tec',
	#
	# 				# TFS (IEEE Transactions on Fuzzy Systems)
	# 				'journals/tfs',
	#
	# 				# TNNLS (IEEE Transactions on Neural Networks and learning systems)
	# 				'journals/tnn',
	#
	# 				# IJAR (International Journal of Approximate Reasoning)
	# 				'journals/ijar',
	#
	# 				# JAIR (Journal of Artificial Intelligence Research)
	# 				'journals/jair',
	#
	# 				#  (Journal of Automated Reasoning)
	# 				'journals/jar',
	#
	# 				# FIXME 无法从dblp获取
	# 				# JSLHR (Journal of Speech, Language, and Hearing Research)
	# 				# 'http://jslhr.pubs.asha.org',
	#
	# 				#  (Machine Learning)
	# 				'journals/ml',
	#
	# 				#  (Neural Computation)
	# 				'journals/neco',
	#
	# 				#  (Neural Networks)
	# 				'journals/nn',
	#
	# 				#  (Pattern Recognition)
	# 				'conf/par',
	#
	# 				# COLT (Annual Conference on Computational Learning Theory)
	# 				'conf/colt',
	#
	# 				# EMNLP (Conference on Empirical Methods in Natural Language Processing)
	# 				'conf/emnlp',
	#
	# 				# ECAI (European Conference on Artificial Intelligence)
	# 				'conf/ecai',
	#
	# 				# ECCV (European Conference on Computer Vision)
	# 				'conf/eccv',
	#
	# 				# ICRA (IEEE International Conference on Robotics and Automation)
	# 				'conf/icra',
	#
	# 				# ICAPS (International Conference on Automated Planning and Scheduling)
	# 				'conf/aips',
	#
	# 				# ICCBR (International Conference on Case-Based Reasoning and Development)
	# 				'conf/iccbr',
	#
	# 				# COLING (International Conference on Computational Linguistics)
	# 				'conf/coling',
	#
	# 				# KR (International Conference on Principles of Knowledge Representation and Reasoning)
	# 				'conf/kr',
	#
	# 				# UAI (International Conference on Uncertainty in Artificial Intelligence)
	# 				'conf/uai',
	#
	# 				# AAMAS (International Joint Conference on Autonomous Agents and Multi-agent Systems)
	# 				'conf/atal',
	#
	# 				# PPSN (Parallel Problem Solving from Nature)
	# 				'conf/ppsn',
	#
	# 			],
	# 		},
	# 		{
	# 			'level': 'C',
	# 			'journals': [
	# 				# TALLIP (ACM Transactions on Asian and Low-Resource Language Information Processing)
	# 				'journals/talip',
	#
	# 				#  (Applied Intelligence)
	# 				'journals/apin',
	#
	# 				# AIM (Artificial Intelligence in Medicine)
	# 				'journals/artmed',
	#
	# 				#  (Artificial Life)
	# 				'journals/alife',
	#
	# 				#  (Computational Intelligence)
	# 				'journals/ci',
	#
	# 				#  (Computer Speech and Language)
	# 				'journals/csl',
	#
	# 				#  (Connection Science)
	# 				'journals/connection',
	#
	# 				# DSS (Decision Support Systems)
	# 				'journals/dss',
	#
	# 				# EAAI (Engineering Applications of Artificial Intelligence)
	# 				'journals/eaai',
	#
	# 				#  (Expert Systems)
	# 				'journals/es',
	#
	# 				# ESWA (Expert Systems with Applications)
	# 				'journals/eswa',
	#
	# 				#  (Fuzzy Sets and Systems)
	# 				'journals/fss',
	#
	# 				# TG (IEEE Transactions on Games)
	# 				'journals/tciaig',
	#
	# 				# IET-CVI (IET Computer Vision)
	# 				'journals/iet-cvi',
	#
	# 				#  (IET Signal Processing)
	# 				'journals/iet-spr',
	#
	# 				# IVC (Image and Vision Computing)
	# 				'journals/ivc',
	#
	# 				# IDA (Intelligent Data Analysis)
	# 				'journals/ida',
	#
	# 				# IJCIA (International Journal of Computational Intelligence and Applications)
	# 				'journals/ijcia',
	#
	# 				# FIXME 前面出现过
	# 				# IJIS (International Journal of Intelligent Systems)
	# 				'journals/ijis',
	#
	# 				# IJNS (International Journal of Neural Systems)
	# 				'journals/ijns',
	#
	# 				# IJPRAI (International Journal of Pattern Recognition and Artificial Intelligence)
	# 				'journals/ijprai',
	#
	# 				# IJUFKS (International Journal of Uncertainty, Fuzziness and Knowledge-Based System)
	# 				'journals/ijufks',
	#
	# 				# IJDAR (International Journal on Document Analysis and Recognition)
	# 				'journals/ijdar',
	#
	# 				# JETAI (Journal of Experimental and Theoretical Artificial Intelligence)
	# 				'journals/jetai',
	#
	# 				# KBS (Knowledge-Based Systems)
	# 				'journals/kbs',
	#
	# 				#  (Machine Translation)
	# 				'journals/mt',
	#
	# 				#  (Machine Vision and Applications)
	# 				'journals/mva',
	#
	# 				#  (Natural Computing)
	# 				'journals/nc',
	#
	# 				# NLE (Natural Language Engineering)
	# 				'journals/nle',
	#
	# 				# NCA (Neural Computing & Applications)
	# 				'journals/nca',
	#
	# 				# NPL (Neural Processing Letters)
	# 				'journals/npl',
	#
	# 				#  (Neurocomputing)
	# 				'journals/ijon',
	#
	# 				# PAA (Pattern Analysis and Applications)
	# 				'journals/paa',
	#
	# 				# PRL (Pattern Recognition Letters)
	# 				'journals/prl',
	#
	# 				#  (Soft Computing)
	# 				'journals/soco',
	#
	# 				# WI (Web Intelligence)
	# 				'journals/wias',
	#
	# 				# AISTATS (Artificial Intelligence and Statistics)
	# 				'conf/aistats',
	#
	# 				# ACCV (Asian Conference on Computer Vision)
	# 				'conf/accv',
	#
	# 				# ACML (Asian Conference on Machine Learning)
	# 				'conf/acml',
	#
	# 				# BMVC (British Machine Vision Conference)
	# 				'conf/bmvc',
	#
	# 				# NLPCC (CCF International Conference on Natural Language Processing and Chinese Computing)
	# 				'conf/nlpcc',
	#
	# 				# CoNLL (Conference on Computational Natural Language Learning)
	# 				'conf/conll',
	#
	# 				# GECCO (Genetic and Evolutionary Computation Conference)
	# 				'conf/gecco',
	#
	# 				# ICTAI (IEEE International Conference on Tools with Artificial Intelligence)
	# 				'conf/ictai',
	#
	# 				# IROS (IEEE\RSJ International Conference on Intelligent Robots and Systems)
	# 				'conf/iros',
	#
	# 				# ALT (International Conference on Algorithmic Learning Theory)
	# 				'conf/alt',
	#
	# 				# ICANN (International Conference on Artificial Neural Networks)
	# 				'conf/icann',
	#
	# 				# FG (International Conference on Automatic Face and Gesture Recognition)
	# 				'conf/fgr',
	#
	# 				# ICDAR (International Conference on Document Analysis and Recognition)
	# 				'conf/icdar',
	#
	# 				# ILP (International Conference on Inductive Logic Programming)
	# 				'conf/ilp',
	#
	# 				# KSEM (International conference on Knowledge Science,Engineering and Management)
	# 				'conf/ksem',
	#
	# 				# ICONIP (International Conference on Neural Information Processing)
	# 				'conf/iconip',
	#
	# 				# ICPR (International Conference on Pattern Recognition)
	# 				'conf/icpr',
	#
	# 				# ICB (International Joint Conference on Biometrics)
	# 				'conf/icb',
	#
	# 				# IJCNN (International Joint Conference on Neural Networks)
	# 				'conf/ijcnn',
	#
	# 				# PRICAI (Pacific Rim International Conference on Artificial Intelligence)
	# 				'conf/pricai',
	#
	# 				# NAACL (The Annual Conference of the North  American Chapter of the Association for Computational Linguistics)
	# 				'conf/naacl',
	#
	# 			],
	# 		},
	# 	],
	# },
	# {
	# 	'name': '人机交互与普适计算',
	# 	'url': 'https://www.ccf.org.cn/Academic_Evaluation/HCIAndPC',
	# 	'levels': [
	# 		{
	# 			'level': 'A',
	# 			'journals': [
	# 				# TOCHI (ACM Transactions on Computer-Human Interaction)
	# 				'journals/tochi',

	# 				# IJHCS (International Journal of Human Computer Studies)
	# 				'journals/ijmms',

	# 				# CSCW (ACM Conference on Computer Supported Cooperative Work and Social Computing)
	# 				'conf/cscw',

	# 				# CHI (ACM Conference on Human Factors in Computing Systems)
	# 				'conf/chi',

	# 				# UbiComp (ACM International Conference on Ubiquitous Computing)
	# 				'conf/huc',

	# 			],
	# 		},
	# 		{
	# 			'level': 'B',
	# 			'journals': [
	# 				# CSCW (Computer Supported Cooperative Work)
	# 				'journals/cscw',

	# 				# HCI (Human Computer Interaction)
	# 				'journals/hhci',

	# 				#  (IEEE Transactions on Human-Machine Systems)
	# 				'journals/thms',

	# 				# IWC (Interacting with Computers)
	# 				'journals/iwc',

	# 				# IJHCI (International Journal of Human-Computer Interaction)
	# 				'journals/ijhci',

	# 				# UMUAI (User Modeling and User-Adapted Interaction)
	# 				'journals/umuai',

	# 				# GROUP (ACM Conference on Supporting Group Work)
	# 				'conf/group',

	# 				# IUI (ACM International Conference on Intelligent User Interfaces)
	# 				'conf/iui',

	# 				# ITS (ACM International Conference on Interactive Tabletops and Surfaces)
	# 				'conf/tabletop',

	# 				# UIST (ACM Symposium on User Interface Software and Technology)
	# 				'conf/uist',

	# 				# ECSCW (European Conference on Computer Supported Cooperative Work)
	# 				'conf/ecscw',

	# 				# PERCOM (IEEE International Conference on Pervasive Computing and Communications)
	# 				'conf/percom',

	# 				# MobileHCI (International Conference on Human Computer Interaction with Mobile Devices and Services)
	# 				'conf/mhci',

	# 			],
	# # 		},
	# 		{
	# 			'level': 'C',
	# 			'journals': [
	# 				# BIT (Behaviour & Information Technology)
	# 				'journals/behaviourIT',

	# 				# PUC (Personal and Ubiquitous Computing)
	# 				'journals/puc',

	# 				# PMC (Pervasive and Mobile Computing)
	# 				'journals/percom',

	# 				# DIS (ACM Conference on Designing Interactive Systems)
	# 				'conf/ACMdis',

	# 				# ICMI (ACM International Conference on Multimodal Interaction)
	# 				'conf/icmi',

	# 				# ASSETS (ACM SIGACCESS Conference on Computers and Accessibility)
	# 				'conf/assets',

	# 				# GI (Graphics Interface conference)
	# 				'conf/graphicsinterface',

	# 				# UIC (IEEE International Conference on Ubiquitous Intelligence and Computing)
	# 				'conf/uic',

	# 				#  (IEEE World Haptics Conference)
	# 				'conf/haptics',

	# 				# INTERACT (IFIP TC13 Conference on Human-Computer Interaction)
	# 				'conf/interact',

	# 				# IDC (Interaction Design and Children)
	# 				'conf/acmidc',

	# 				# CollaborateCom (International Conference on Collaborative Computing: Networking, Applications and Worksharing)
	# 				'conf/colcom',

	# 				# CSCWD (International Conference on Computer Supported Cooperative Work in Design)
	# 				'conf/cscwd',

	# 				# CoopIS (International Conference on Cooperative Information Systems)
	# 				'conf/coopis',

	# 				# MobiQuitous (International Conference on Mobile and Ubiquitous Systems: Computing,Networking and Services)
	# 				'conf/mobiquitous',

	# 				# AVI (International Working Conference on Advanced Visual Interfaces)
	# 				'conf/avi',

	# 			],
	# 		},
	# 	],
	# },
	# {
	# 	'name': '交叉/综合/新兴',
	# 	'url': 'https://www.ccf.org.cn/Academic_Evaluation/Cross_Compre_Emerging',
	# 	'levels': [
	# 		{
	# 			'level': 'A',
	# 			'journals': [
	# 				# JACM (Journal of the ACM)
	# 				'journals/jacm',

	# 				# Proc. IEEE (Proceedings of the IEEE)
	# 				'journals/pieee',

	# 				# WWW (International World Wide Web Conferences)
	# 				'conf/www',

	# 				# RTSS (Real-Time Systems Symposium)
	# 				'conf/rtss',

	# 			],
	# 		},
	# 		{
	# 			'level': 'B',
	# 			'journals': [
	# 				#  (Bioinformatics)
	# 				'journals/bioinformatics',

	# 				#  (Briefings in Bioinformatics)
	# 				'journals/bib',

	# 				# FIXME 无法从dblp获取
	# 				# Cognition (Cognition：International Journal of Cognitive Science)
	# 				# 'http://www.journals.elsevier.com/cognition',

	# 				# TASAE (IEEE Transactions on Automation Science and Engineering)
	# 				'journals/tase',

	# 				# TGARS (IEEE Transactions on Geoscience and Remote Sensing)
	# 				'journals/tgrs',

	# 				# TITS (IEEE Transactions on Intelligent Transportation Systems)
	# 				'journals/tits',

	# 				# TMI (IEEE Transactions on Medical Imaging)
	# 				'journals/tmi',

	# 				# TR (IEEE Transactions on Robotics)
	# 				'journals/trob',

	# 				# TCBB (IEEE-ACM Transactions on Computational Biology and Bioinformatics)
	# 				'journals/tcbb',

	# 				# JCST (Journal of Computer Science and Technology)
	# 				'journals/jcst',

	# 				# JAMIA (Journal of the American Medical Informatics Association)
	# 				'journals/jamia',

	# 				#  (PLOS Computational Biology)
	# 				'journals/ploscb',

	# 				#  (Science China Information Sciences)
	# 				'journals/chinaf',

	# 				#  (The Computer Journal)
	# 				'journals/cj',

	# 				#  (World Wide Web Journal)
	# 				'journals/wwwj',

	# 				# CogSci (Cognitive Science Society Annual Conference)
	# 				'conf/cogsci',

	# 				# BIBM (IEEE International Conference on Bioinformatics and Biomedicine)
	# 				'conf/bibm',

	# 				# EMSOFT (International Conference on Embedded Software)
	# 				'conf/emsoft',

	# 				# FIXME 无法从dblp获取
	# 				# ISMB (International conference on Intelligent Systems for Molecular Biology)
	# 				# 'http://www.iscb.org/about-ismb',

	# 				# RECOMB (International Conference on Research in Computational Molecular Biology)
	# 				'conf/recomb',

	# 			],
	# 		},
	# 		{
	# 			'level': 'C',
	# 			'journals': [
	# 				#  (BMC Bioinformatics)
	# 				'journals/bmcbi',

	# 				#  (Cybernetics and Systems)
	# 				'journals/cas',

	# 				# FCS (Frontiers of Computer Science)
	# 				'journals/fcsc',

	# 				#  (IEEE Geoscience and Remote Sensing Letters)
	# 				'journals/lgrs',

	# 				# JBHI (IEEE Journal of Biomedical and Health Informatics)
	# 				'journals/titb',

	# 				# TBD (IEEE Transactions on Big Data)
	# 				'journals/tbd',

	# 				# FIXME 无法从dblp获取
	# 				#  (IET Intelligent Transport Systems)
	# 				# 'http://digital-library.theiet.org/content/journals/iet-its',

	# 				# JBI (Journal of Biomedical Informatics)
	# 				'journals/jbi',

	# 				#  (Medical Image Analysis)
	# 				'journals/mia',

	# 				# AMIA (American Medical Informatics Association Annual Symposium)
	# 				'conf/amia',

	# 				# APBC (Asia Pacific Bioinformatics Conference)
	# 				'conf/apbc',

	# 				#  (IEEE International Conference on Big Data)
	# 				'conf/bigdataconf',

	# 				#  (IEEE International Conference on Cloud Computing)
	# 				'conf/IEEEcloud',

	# 				# SMC (IEEE International Conference on Systems, Man, and Cybernetics)
	# 				'conf/smc',

	# 				# COSIT (International Conference on Spatial Information Theory)
	# 				'conf/cosit',

	# 				# ISBRA (International Symposium on Bioinformatics Research and Applications)
	# 				'conf/isbra',

	# 			],
	# 		},
	# 	],
	# }
]


# 返回期刊会议生成器
def journals_generator():
	for domain in ccf:
		domain_name = domain['name']
		# print(domain_name)
		levels = domain['levels']
		for level in levels:
			for journal in level['journals']:
				yield journal


if __name__ == '__main__':
	def get_all_journals():
		''' 获取所有的会议\期刊

		:return:
		'''
		for domain in domains:
			journals = get_journals(domain['name'], domain['url'], ['A', 'B', 'C'])
			print('{}: {}'.format(domain['name'], len(journals)))

	get_all_journals()

	from queue import Queue
	import threading
	from threading import Lock

	# ccf人工智能和计算机体系结构所有会议期刊从2001-2020的论文数量
	# 需要去重
	journal_paper_num = {
		'conf/asiaccs': 791,
		'conf/codes': 801,
		'conf/cnhpca': 107,
		'journals/trets': 335,
		'conf/icdcs': 2047,
		'conf/sigmetrics': 1054,
		'conf/iccad': 2493,
		'journals/taas': 307,
		'conf/ppopp': 787,
		'conf/parco': 809,
		'conf/isca': 881,
		'conf/cluster': 1517,
		'conf/spaa': 889,
		'conf/usenix': 630,
		'conf/IEEEpact': 217,
		'conf/fast': 439,
		'conf/iccd': 1788,
		'conf/fpga': 1214,
		'journals/tocs': 209,
		'conf/podc': 1242,
		'journals/tos': 318,
		'conf/sc': 1685,
		'journals/taco': 692,
		'conf/cloud': 468,
		'journals/tvlsi': 4112,
		'conf/dac': 3670,
		'conf/hipeac': 149,
		'journals/tecs': 1304,
		'conf/eurosys': 497,
		'conf/icpp': 1470,
		'journals/todaes': 995,
		'conf/asplos': 752,
		'journals/tc': 3264,
		'journals/micro': 1306,
		'conf/lisa': 565,
		'conf/ics': 821,
		'conf/cgo': 529,
		'journals/dc': 480,
		'journals/tcc': 399,
		'journals/tpds': 3499,
		'journals/tcad': 3495,
		'conf/performance': 21,
		'journals/jetc': 467,
		'conf/date': 5252,
		'conf/europar': 1677,
		'conf/vee': 288,
		'conf/rtas': 684,
		'conf/fpl': 2420,
		'conf/cf': 846,
		'conf/itc': 2057,
		'conf/hpdc': 766,
		'conf/asap': 872,
		'conf/mss': 67,
		'conf/ets': 701,
		'conf/npc': 641,
		'conf/hpcc': 2840,
		'conf/aspdac': 3071,
		'conf/nocs': 405,
		'conf/glvlsi': 1622,
		'conf/systor': 277,
		'conf/ccgrid': 2180,
		'conf/fccm': 1043,
		'journals/concurrency': 3636,
		'conf/islped': 1425,
		'conf/ica3pp': 335,
		'conf/mascots': 1061,
		'conf/hipc': 954,
		'conf/icpads': 2024,
		'conf/ipps': 4495,
		'conf/nsdi': 638,
		'conf/cases': 547,
		'conf/fpt': 1182,
		'conf/ispa': 1673,
		'conf/vts': 1192,
		'conf/ats': 1162,
		'journals/rts': 496,
		'journals/tosn': 583,
		'journals/tmc': 2635,
		'conf/mobicom': 1081,
		'journals/tomccap': 752,
		'conf/mobihoc': 790,
		'journals/jsac': 3920,
		'conf/hoti': 348,
		'conf/infocom': 5807,
		'conf/imc': 702,
		'conf/sigcomm': 987,
		'journals/ppna': 821,
		'conf/ipsn': 1057,
		'journals/ton': 2807,
		'conf/mobisys': 926,
		'conf/ispd': 681,
		'journals/toit': 441,
		'journals/mam': 1641,
		'conf/iscas': 12198,
		'journals/tcom': 7221,
		'conf/conext': 676,
		'journals/iet-com': 3899,
		'conf/iwqos': 811,
		'conf/secon': 1252,
		'journals/tnsm': 753,
		'conf/icnp': 1018,
		'conf/sensys': 1221,
		'conf/nossdav': 372,
		'journals/twc': 8461,
		'journals/wicomm': 2881,
		'conf/ancs': 456,
		'conf/lcn': 2332,
		'journals/integration': 1163,
		'conf/apnoms': 1061,
		'journals/monet': 1648,
		'conf/forte': 450,
		'journals/jsa': 1303,
		'conf/wowmom': 1681,
		'conf/icccn': 2547,
		'journals/jpdc': 2483,
		'conf/mass': 1680,
		'conf/ccs': 1996,
		'conf/ipccc': 1295,
		'conf/hotnets': 355,
		'journals/tdsc': 782,
		'conf/networking': 1247,
		'conf/wcnc': 9114,
		'journals/winet': 2556,
		'conf/eurocrypt': 512,
		'conf/msn': 968,
		'journals/tjs': 3287,
		'conf/wasa': 801,
		'conf/sp': 742,
		'journals/tifs': 2310,
		'conf/mswim': 890,
		'conf/crypto': 460,
		'conf/p2p': 553,
		'journals/fgcs': 4658,
		'conf/iscc': 3520,
		'journals/jcs': 484,
		'conf/ches': 569,
		'conf/srds': 727,
		'conf/im': 1431,
		'journals/iet-ifs': 568,
		'journals/ijics': 241,
		'conf/csfw': 195,
		'journals/joc': 457,
		'journals/tissec': 379,
		'conf/fse': 448,
		'conf/icc': 18399,
		'journals/scn': 2260,
		'conf/acsac': 909,
		'journals/networks': 1087,
		'conf/ndss': 741,
		'conf/ctrsa': 546,
		'journals/ijisp': 267,
		'conf/wisec': 387,
		'conf/uss': 897,
		'conf/sacmat': 515,
		'journals/imcs': 550,
		'conf/asiacrypt': 477,
		'journals/ejisec': 179,
		'conf/raid': 468,
		'conf/pkc': 477,
		'conf/drm': 134,
		'conf/dsn': 1373,
		'conf/sec': 742,
		'conf/esorics': 424,
		'conf/globecom': 17527,
		'conf/fc': 605,
		'conf/acisp': 637,
		'conf/dfrws': 14,
		'conf/acns': 577,
		'conf/tcc': 381,
		'conf/ih': 246,
		'journals/iee': 159,
		'conf/isw': 619,
		'conf/securecomm': 500,
		'conf/icdf2c': 141,
		'conf/dimva': 258,
		'conf/icics': 775,
		'conf/soups': 360,
		'conf/pet': 116,
		'conf/pam': 432,
		'conf/sigsoft': 1460,
		'conf/sosp': 284,
		'conf/trustcom': 1802,
		'journals/tse': 1333,
		'conf/issta': 590,
		'conf/oopsla': 844,
		'journals/tosem': 389,
		'journals/toplas': 435,
		'conf/pldi': 931,
		'conf/nspw': 258,
		'conf/icse': 2339,
		'conf/popl': 736,
		'conf/kbse': 1736,
		'journals/smr': 793,
		'journals/tsc': 673,
		'journals/ese': 913,
		'conf/sacrypt': 512,
		'journals/istr': 813,
		'journals/jfp': 543,
		'conf/caap': 0,
		'journals/ase': 378,
		'journals/jlp': 0,
		'conf/iwpc': 186,
		'conf/tapsoft': 0,
		'conf/osdi': 309,
		'conf/models': 644,
		'journals/stvr': 431,
		'conf/lctrts': 425,
		'conf/cc': 394,
		'conf/esop': 606,
		'conf/icws': 1954,
		'conf/icfp': 544,
		'conf/vmcai': 525,
		'conf/caise': 860,
		'journals/sosym': 858,
		'conf/re': 1206,
		'journals/re': 412,
		'conf/hotos': 312,
		'conf/icsm': 1069,
		'conf/esem': 776,
		'conf/wcre': 591,
		'conf/issre': 743,
		'conf/middleware': 429,
		'conf/sas': 502,
		'conf/ecoop': 546,
		'journals/spe': 1505,
		'journals/soca': 285,
		'journals/compsec': 1971,
		'conf/icsoc': 952,
		'journals/dcc': 2167,
		'journals/sttt': 694,
		'conf/paste': 123,
		'conf/fm': 485,
		'conf/iceccs': 668,
		'journals/adhoc': 2027,
		'journals/jwe': 367,
		'conf/apsec': 1302,
		'conf/ispw': 42,
		'conf/cp': 1341,
		'conf/pepm': 300,
		'journals/cl': 320,
		'conf/tools': 35,
		'conf/tase': 452,
		'conf/ispass': 558,
		'journals/tplp': 714,
		'conf/seke': 2460,
		'conf/compsac': 1470,
		'conf/icfem': 651,
		'conf/refsq': 341,
		'conf/icwe': 1068,
		'conf/icst': 737,
		'conf/aplas': 518,
		'journals/ijseke': 1073,
		'conf/ease': 468,
		'conf/IEEEscc': 1593,
		'conf/qrs': 235,
		'journals/sqj': 626,
		'conf/icsr': 339,
		'journals/tweb': 281,
		'conf/spin': 396,
		'conf/msr': 781,
		'conf/lopstr': 321,
		'conf/atva': 583,
		'journals/tods': 489,
		'conf/wicsa': 501,
		'conf/scam': 468,
		'journals/cn': 4676,
		'journals/jnca': 2424,
		'journals/vldb': 719,
		'journals/tkde': 3087,
		'conf/semweb': 55,
		'journals/tkdd': 474,
		'conf/sigmod': 2796,
		'conf/wsdm': 1101,
		'conf/icdm': 2804,
		'journals/geoinformatica': 475,
		'conf/pods': 622,
		'journals/jasis': 3797,
		'conf/vldb': 941,
		'conf/icde': 3524,
		'journals/ejis': 845,
		'conf/kdd': 3340,
		'journals/tois': 488,
		'conf/icdt': 424,
		'journals/ipm': 1573,
		'conf/ecml': 439,
		'conf/sigir': 3707,
		'conf/cidr': 486,
		'journals/infsof': 2106,
		'conf/sdm': 1625,
		'journals/comcom': 4528,
		'journals/datamine': 750,
		'conf/cikm': 4890,
		'conf/esws': 34,
		'journals/jcis': 903,
		'conf/dasfaa': 593,
		'journals/jdm': 313,
		'journals/aei': 1083,
		'conf/edbt': 1316,
		'journals/ijswis': 260,
		'conf/ecir': 1317,
		'conf/dexa': 799,
		'journals/iam': 1246,
		'journals/gis': 1751,
		'journals/ijcis': 324,
		'conf/er': 886,
		'journals/ijis': 1401,
		'journals/dpd': 389,
		'journals/ir': 497,
		'journals/jsis': 430,
		'conf/webdb': 244,
		'journals/ijkm': 309,
		'conf/apweb': 925,
		'conf/ssd': 329,
		'conf/ssdbm': 799,
		'conf/wise': 648,
		'conf/waim': 1054,
		'conf/soda': 2911,
		'journals/tocl': 552,
		'journals/ws': 508,
		'conf/pakdd': 835,
		'journals/talg': 720,
		'journals/toms': 606,
		'journals/fac': 612,
		'journals/tit': 8721,
		'conf/cav': 811,
		'conf/focs': 1495,
		'journals/mscs': 846,
		'conf/concur': 746,
		'conf/hybrid': 847,
		'conf/stoc': 1837,
		'conf/cade': 378,
		'conf/mdm': 999,
		'conf/compgeom': 1222,
		'conf/lics': 1114,
		'journals/siamcomp': 1447,
		'journals/jiis': 706,
		'conf/esa': 1306,
		'journals/cc': 333,
		'journals/fmsd': 467,
		'conf/coco': 629,
		'journals/kais': 1598,
		'conf/icalp': 1188,
		'journals/lisp': 187,
		'journals/informs': 939,
		'journals/is': 1193,
		'conf/sat': 640,
		'journals/jss': 3387,
		'journals/acta': 472,
		'conf/fmcad': 522,
		'journals/logcom': 1103,
		'conf/dsaa': 542,
		'journals/jsyml': 1544,
		'conf/fsttcs': 851,
		'conf/mfcs': 1184,
		'conf/rta': 452,
		'conf/isaac': 1380,
		'journals/siamdm': 1979,
		'conf/ipco': 482,
		'conf/csl': 840,
		'conf/mm': 4691,
		'conf/stacs': 1183,
		'conf/ictac': 450,
		'conf/siggraph': 209,
		'journals/tvcg': 3551,
		'conf/visualization': 542,
		'journals/mst': 1212,
		'journals/dke': 1233,
		'journals/siamis': 823,
		'journals/tog': 3344,
		'conf/vr': 2293,
		'journals/cgf': 3489,
		'journals/ipl': 3716,
		'journals/jc': 847,
		'journals/jcss': 1517,
		'journals/tip': 6392,
		'journals/algorithmica': 2154,
		'journals/jgo': 2333,
		'journals/tmm': 2828,
		'conf/si3d': 531,
		'conf/dcc': 1854,
		'journals/iet-ipr': 1343,
		'conf/mir': 340,
		'conf/vissym': 138,
		'conf/sgp': 134,
		'conf/sma': 182,
		'conf/ismar': 1050,
		'journals/lmcs': 988,
		'conf/sca': 493,
		'conf/rt': 242,
		'conf/eurographics': 0,
		'journals/jvca': 935,
		'conf/pg': 305,
		'journals/mms': 757,
		'journals/tcsv': 3424,
		'journals/spl': 4770,
		'journals/apal': 1637,
		'conf/icmcs': 6257,
		'conf/cgi': 472,
		'journals/jsc': 1535,
		'conf/vrst': 1067,
		'conf/ca': 86,
		'conf/interspeech': 14696,
		'conf/apvis': 137,
		'conf/cadgraphics': 552,
		'conf/gmp': 205,
		'conf/3dim': 0,
		'journals/cvgip': 511,
		'conf/smi': 407,
		'conf/pcm': 993,
		'journals/cagd': 1129,
		'journals/tslp': 84,
		'journals/iandc': 1500,
		'journals/vc': 2037,
		'conf/mmm': 571,
		'conf/icassp': 19444,
		'conf/acl': 1514,
		'journals/scp': 1931,
		'conf/icip': 12387,
		'journals/pami': 3670,
		'conf/nips': 7795,
		'conf/ijcai': 6590,
		'journals/tap': 401,
		'journals/jmlr': 2146,
		'conf/cvpr': 8122,
		'journals/dcg': 1619,
		'journals/cg': 1950,
		'conf/iccv': 3721,
		'journals/ec': 457,
		'conf/icml': 4749,
		'journals/coling': 619,
		'journals/taffco': 374,
		'journals/tnn': 4188,
		'journals/tec': 1101,
		'journals/tfs': 2403,
		'conf/aaai': 9995,
		'journals/spic': 1751,
		'journals/neco': 2121,
		'journals/aamas': 611,
		'journals/tcyb': 2195,
		'journals/taslp': 3175,
		'conf/par': 0,
		'journals/comgeo': 1025,
		'conf/eccv': 0,
		'conf/colt': 1034,
		'conf/ecai': 1871,
		'conf/emnlp': 2935,
		'conf/uai': 1619,
		'journals/cad': 2152,
		'conf/kr': 673,
		'conf/atal': 35,
		'journals/jvcir': 2219,
		'conf/icra': 14636,
		'journals/fuin': 2936,
		'conf/iccbr': 562,
		'journals/mta': 8517,
		'conf/aips': 35,
		'journals/iet-cvi': 631,
		'conf/coling': 1792,
		'journals/talip': 490,
		'journals/tciaig': 356,
		'journals/es': 776,
		'journals/sigpro': 5666,
		'journals/ci': 576,
		'journals/speech': 1623,
		'journals/alife': 542,
		'journals/iet-spr': 907,
		'conf/ppsn': 622,
		'journals/mt': 290,
		'journals/ijprai': 1822,
		'journals/jair': 1017,
		'journals/ijcia': 474,
		'journals/ida': 1066,
		'journals/ijufks': 1147,
		'journals/jetai': 629,
		'journals/jar': 659,
		'journals/nc': 827,
		'journals/apin': 1779,
		'journals/mva': 1202,
		'journals/connection': 385,
		'journals/ijdar': 438,
		'journals/ijcv': 1729,
		'journals/nca': 4318,
		'journals/wias': 407,
		'conf/aistats': 1384,
		'conf/acml': 335,
		'conf/nlpcc': 324,
		'journals/paa': 973,
		'journals/ijns': 844,
		'journals/csl': 886,
		'conf/bmvc': 2620,
		'journals/nle': 515,
		'journals/npl': 1397,
		'conf/accv': 0,
		'journals/ml': 1166,
		'conf/gecco': 3887,
		'conf/icann': 723,
		'conf/conll': 649,
		'journals/soco': 4981,
		'conf/ictai': 2243,
		'conf/alt': 646,
		'conf/fgr': 319,
		'conf/icb': 788,
		'conf/iconip': 211,
		'conf/pricai': 856,
		'journals/dam': 5821,
		'journals/eaai': 2730,
		'conf/icdar': 2581,
		'conf/ilp': 417,
		'conf/ksem': 545,
		'journals/tochi': 509,
		'conf/iros': 15151,
		'journals/thms': 547,
		'conf/naacl': 1574,
		'conf/icpr': 5220,
		'journals/iwc': 857,
		'conf/huc': 0,
		'journals/umuai': 308,
		'journals/cscw': 459,
		'conf/ijcnn': 8584,
		'journals/hhci': 281,
		'conf/group': 532,
		'conf/chi': 6929,
		'conf/cscw': 1318,
		'journals/ijhci': 1192,
		'conf/ecscw': 195,
		'conf/mhci': 1473,
		'conf/iui': 1369,
		'conf/uist': 1038,
		'journals/ijar': 1916,
		'conf/percom': 740,
		'conf/assets': 1266,
		'conf/icmi': 1458,
		'journals/puc': 1459,
		'journals/ivc': 2084,
		'conf/haptics': 807,
		'conf/acmidc': 1262,
		'journals/behaviourIT': 1349,
		'conf/coopis': 219,
		'journals/tase': 1635,
		'journals/nn': 2918,
		'conf/interact': 529,
		'journals/wwwj': 0,
		'journals/artmed': 1232,
		'conf/tabletop': 93,
		'conf/mobiquitous': 869,
		'conf/uic': 2209,
		'conf/cscwd': 2364,
		'journals/cviu': 1935,
		'conf/avi': 840,
		'conf/ACMdis': 1002,
		'journals/pieee': 2620,
		'journals/bib': 1415,
		'conf/colcom': 961,
		'conf/rtss': 798,
		'conf/graphicsinterface': 618,
		'journals/tbd': 217,
		'journals/jacm': 746,
		'journals/tcbb': 1787,
		'journals/tmi': 3667,
		'journals/trob': 2274,
		'journals/ai': 1446,
		'journals/chinaf': 3513,
		'conf/www': 3263,
		'conf/apbc': 240,
		'journals/jcst': 1914,
		'journals/ploscb': 5814,
		'journals/dss': 3200,
		'journals/cj': 2020,
		'journals/tits': 3135,
		'journals/jamia': 2803,
		'conf/cogsci': 7354,
		'conf/bibm': 3318,
		'journals/cas': 785,
		'journals/fcsc': 975,
		'conf/emsoft': 545,
		'conf/IEEEcloud': 1290,
		'conf/cosit': 283,
		'journals/bioinformatics': 12980,
		'journals/titb': 2548,
		'conf/recomb': 824,
		'journals/lgrs': 4585,
		'conf/bigdataconf': 3783,
		'conf/isbra': 467,
		'journals/tgrs': 8578,
		'journals/ijmms': 1488,
		'conf/amia': 8080,
		'journals/eswa': 12262,
		'journals/bmcbi': 9876,
		'conf/smc': 12170,
		'journals/mia': 1616,
		'journals/prl': 5065,
		'journals/percom': 1067,
		'journals/jbi': 2269,
		'journals/isci': 8910,
		'journals/kbs': 4068,
		'journals/fss': 4435,
		'journals/ijon': 13339,
		'journals/tcs': 8901,
	}


	# 爬取各个期刊会议的论文数量
	def main():
		journals_queue = Queue()
		for journal in journals_generator():
			journals_queue.put(journal)

		def __do_task(queue, lock: Lock):
			global journal_paper_num
			while not queue.empty():
				journal = queue.get()
				papers = []
				if journal.startswith('journals/'):
					papers = get_journals_papers(journal)
				elif journal.startswith('conf/'):
					papers = get_conf_papers(journal)

				num = len(list(papers))

				# lock.acquire()
				# journal_paper_num[journal] = num
				print('\'{}\': {}'.format(journal, num))
			# with open('./ccf_paper_num.txt', 'w', encoding='utf-8') as f:
			# 	f.write(json.dumps(journal_paper_num, indent=4))
			# lock.release()

		lock = Lock()
		ths = []
		for i in range(40):
			th = threading.Thread(target=__do_task, args=(journals_queue, lock))
			th.start()
			ths.append(th)

		for th in ths:
			th.join()


	# 统计输出ccf每个领域每个类别的论文数量
	def count_papers():
		total_journals_num = 0
		total_papers_num = 0

		for domain in ccf:
			domain_name = domain['name']
			print(domain_name)
			domain_journals_num = 0
			domain_papers_num = 0
			for level in domain['levels']:
				print('    {}类'.format(level['level']))

				journals_num = len(level['journals'])
				level_papers_num = 0
				for journal in level['journals']:
					journal_papers_num = journal_paper_num.get(journal, 0)
					print('        {}: {}'.format(journal, journal_papers_num))
					level_papers_num += journal_papers_num

				domain_papers_num += level_papers_num
				print('    {}类共有: {}journals, {}papers'.format(level['level'], journals_num, level_papers_num))
				domain_journals_num += journals_num

			print('{} has total {} journals, {}papers'.format(domain_name, domain_journals_num, domain_papers_num))
			total_journals_num += domain_journals_num
			total_papers_num += domain_papers_num

		print('total journals num: {}, total papers num: {}'.format(total_journals_num, total_papers_num))


	# count_papers()
	# main()
