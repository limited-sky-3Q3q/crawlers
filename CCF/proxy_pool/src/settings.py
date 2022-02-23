# redis
REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
REDIS_PASSWORD = None

# 基本测试的url地址
BASE_CHECK_WEBSITE = 'https://www.baidu.com'

# httpbin, 用来检测代理高匿, 返回的origin字段中只包含代理ip或者不包含本机ip就判断为高匿
HTTPBIN_URL = 'https://httpbin.org/ip'

# 日志目录
LOG_FOLDER = '../log/'

# 需要测试的网站
CHECK_WEBSITES = {
	'ieee': {
		'url': 'https://ieeexplore.ieee.org/',
		'test_cycle': 45,
		'min_sleep_time_after_use': 10,
		'max_sleep_time_after_use': 15,
	},
	'acm': {
		'url': 'https://dl.acm.org/',
		'test_cycle': 45,
		'min_sleep_time_after_use': 10,
		'max_sleep_time_after_use': 15,
	},
	'springer': {
		'url': 'https://link.springer.com/',
		'test_cycle': 45,
		'min_sleep_time_after_use': 10,
		'max_sleep_time_after_use': 15,
	},
	'sciencedirect': {
		'url': 'https://www.sciencedirect.com',
		'test_cycle': 45,
		'min_sleep_time_after_use': 10,
		'max_sleep_time_after_use': 15,
	},
	'doi': {
		'url': 'https://doi.org',
		'test_cycle': 45,
		'min_sleep_time_after_use': 10,
		'max_sleep_time_after_use': 15,
	},
    'aaai': {
        'url': 'https://aaai.org',
        'test_cycle': 45,
        'min_sleep_time_after_use': 10,
        'max_sleep_time_after_use': 15,
    },
    'researchgate': {
        'url': 'https://www.researchgate.net/',
        'test_cycle': 45,
        'min_sleep_time_after_use': 25,
        'max_sleep_time_after_use': 40,
     },
    'usenix': {
        'url': 'https://www.usenix.org/',
        'test_cycle': 45,
        'min_sleep_time_after_use': 10,
        'max_sleep_time_after_use': 15,
    },
    'aminer': {
        'url': 'https://www.aminer.cn',
        'test_cycle': 60,
        'min_sleep_time_after_use': 30,
        'max_sleep_time_after_use': 45,
    },
    'dblp': {
        'url': 'https://dblp.org',
        'test_cycle': 45,
        'min_sleep_time_after_use': 5,
        'max_sleep_time_after_use': 20,
    }
}

# 获取的代理的scheme(http, https, both)
PROXY_SCHEME = 'https'

# proxy使用一次后休眠时间
PROXY_MIN_SLEEP_TIME = 5
PROXY_MAX_SLEEP_TIME = 15

# proxy api
SERVER_API = {
	'host': '0.0.0.0',
	'port': 5010
}

# 代理获取器的设置
PROXY_GETTER_SETTINGS = {
	'FreeipProxy': {
		'enable': True,
		'args': {
			'scheme': PROXY_SCHEME,
		}
	},
	'MipuProxy': {
		'enable': True,
		'args': {
			'scheme': PROXY_SCHEME,
		}
	},
	'XilaProxy': {
		'enable': True,
		'args': {
			'scheme': PROXY_SCHEME,
		}
	},
	'XICIProxy': {
		'enable': True,
		'args': {
			'page_start': 1,
			'page_end': 2,
			'scheme': PROXY_SCHEME,
		}
	},
	'YunProxy': {
		'enable': True,
		'args': {
			'scheme': PROXY_SCHEME,
		}
	},
	'WuyouProxy': {
		'enable': True,
		'args': {
			'scheme': 'both',
		}
	},
	'KuaiProxy': {
		'enable': True,
		'args': {
			'scheme': 'http',
		}
	},
	'QiyunProxy': {
		'enable': True,
		'args': {
			'scheme': PROXY_SCHEME,
		}
	},
	'IphaiProxy': {
		'enable': True,
		'args': {
			'scheme': PROXY_SCHEME,
		}
	},
	'GoubanjiaProxy': {
		'enable': True,
		'args': {
			'scheme': 'both',
		}
	}
}
