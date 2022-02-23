from urllib.request import Request
from urllib.request import urlopen
from urllib.parse import quote  # 中文转url编码
import urllib
import random
import re


# 获取新鲜的IP代理地址
def get_proxies():
    total_proxies = []
    pattern = re.compile(r"(((?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}"
                         r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d))"
                         r"(</td><td>))(\d|){5})")
    for i in range(1, 10):
        temp = urlopen("http://www.66ip.cn/{}.html".format(i))
        temp = pattern.findall(temp.read().decode("gbk"))
        for a, b in enumerate(temp):
            temp[a] = b[0].replace("</td><td>", ":")
        total_proxies += temp
    if total_proxies is False:
        print("IP proxies is empty!")
    # print()
    return total_proxies


# 根据提供的url获取html文件
def get_html(url, proxies, with_proxy=False):
    if with_proxy:
        proxy = random.choice(proxies)  # 随机取一个ip出来使用
        print("use proxy:", proxy)
        proxy_support = urllib.request.ProxyHandler({"http": proxy})
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        return opener.open(url, timeout=5, cookie="")
    else:  # 无代理
        print("!!!")
        return urlopen(url)


#  爬虫类基类
class BaseCrawler:
    def __init__(self, url):
        self.url = url  # 爬取的链接
        self.proxies = []  # IP代理

    # 获取网页
    def get_html(self, with_proxy=False):
        print("url:", self.url)
        print("with proxy:", with_proxy)
        return get_html(self.url, self.proxies, with_proxy=with_proxy)

    # 设置搜索条件
    def set(self):
        return

    # 更改url
    def change_url(self, url):
        self.url = url
        return

    # 更新IP代理
    def update_proxies(self):
        print("update proxies")
        self.proxies = get_proxies()
        print("new proxies:", self.proxies)
        return


#  微博关键字爬虫
#  根据搜索关键词和指定搜索范围爬取网站
#  微博的文件编码格式是gb2312
#  微博不封IP，只封账号，不需要使用IP代理
#  需要加上多个账号cookie，没有cookie时，爬取到的html文件是登录界面
class WeiboKeywordCrawler(BaseCrawler):
    def __init__(self):
        self.query = "搜索关键字"  # 搜索关键字
        self.weibo_types = {"全部": "typeall=1", "热门": "xsort=hot", "原创": "scope=ori", "关注人": "atten=1",
                            "认证用户": "vip=1", "媒体": "category=4", "观点": "viewpoint=1"}  # 搜索类型
        self.includings = {"全部": "suball=1", "含图片": "haspic=1", "含视频": "hasvideo=1",
                           "含音乐": "hasmusic=1", "含短链": "haslink=1"}  # 包含文件类型
        self.time_scope = ["{year}-{month}-{day}".format(year=2000, month=1, day=1),
                           "{year}-{month}-{day}".format(year=2022, month=2, day=4)]  # 时间范围

        self.weibo_type = self.weibo_types["全部"]
        self.including = self.includings["全部"]
        self.page = 1

        self.url = "https://s.weibo.com/weibo?" \
                   "q={}&{}&{}&timescope=custom:{}:{}&Refer=g&&page={}".format(quote(self.query),
                                                                               self.weibo_type,
                                                                               self.including,
                                                                               self.time_scope[0],
                                                                               self.time_scope[1],
                                                                               self.page)
        super(WeiboKeywordCrawler, self).__init__(self.url)  # 初始化基类属性

    # 设置搜索条件
    def set(self, weibo_type="全部", including="全部", time_scope=[2000, 1, 1, 2022, 2, 4], page=1):
        self.weibo_type = self.weibo_types[weibo_type]
        self.including = self.includings[including]
        self.time_scope = ["{year}-{month}-{day}".format(year=time_scope[0], month=time_scope[1], day=time_scope[2]),
                           "{year}-{month}-{day}".format(year=time_scope[3], month=time_scope[4], day=time_scope[5])]
        self.page = page
        self.url = "https://s.weibo.com/weibo?" \
                   "q={}&{}&{}&timescope=custom:{}:{}&Refer=g&&page={}".format(quote(self.query),
                                                                               self.weibo_type,
                                                                               self.including,
                                                                               self.time_scope[0],
                                                                               self.time_scope[1],
                                                                               self.page)

    # 更改url
    def change_url(self, url):
        self.url = url
        return

