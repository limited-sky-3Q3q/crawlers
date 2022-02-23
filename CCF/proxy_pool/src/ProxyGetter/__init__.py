from .xiciProxy import XICIProxy
from .yunProxy import YunProxy
from .wuyouProxy import WuyouProxy
from .kuaiProxy import KuaiProxy
from .iphaiProxy import IphaiProxy
from .freeipProxy import FreeipProxy
from .qiyunProxy import QiyunProxy
from .mipuProxy import MipuProxy
from .xilaProxy import XilaProxy
from .goubanjiaProxy import GoubanjiaProxy


# 代理爬取器集合，新增代理爬取器需添加到该列表中
proxy_getter_list = [
	# 大量可用
	# FreeipProxy,
	MipuProxy,
	XilaProxy,

	# 几乎无可用
	XICIProxy,
	YunProxy,
	WuyouProxy,
	# IphaiProxy,
	QiyunProxy,
	GoubanjiaProxy,

	# 全是http, 稍微会有几个http/https
	KuaiProxy,

]