# # coding:utf-8
# import crawler
# from bs4 import BeautifulSoup
# from time import sleep
# from html.parser import HTMLParser
# # proxies = crawler.get_proxies()  # 新鲜的ip代理
# #
# # url = "http://www.baidu.com"
# # print(proxies)
#
#
# test = crawler.WeiboKeywordCrawler()
# print(test.query, test.url, test.proxies, test.including, test.time_scope, test.weibo_type)
# test.update_proxies()
# # print(test.get_html().info())
# page = 1
# while page <= 50:
#     try:
#         print("--------------------------------begin line--------------------------------")
#         test.set(page=page)
#         html = test.get_html(with_proxy=False)
#         # print(html.read().decode("gb2312"))
#         soup = BeautifulSoup(html, "html.parser", from_encoding='gb2312')
#         print(soup)
#         # print(HTMLParser.feed(html.read().encode("utf-8")))
#         print("html page:", test.page)
#         page += 1
#         print("--------------------------------end line--------------------------------")
#         sleep(3)
#     except:
#         print("故障")
#
# print("finish!")
#


# -*- coding:utf-8 -*-
# Author: Suummmmer
# Date: 2019-05-17

import requests
import random

headers = {
"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
"like Gecko) Chrome/69.0.3497.100 Safari/537.36",
}

def get_tid():
    """
    获取tid,c,w
    :return:tid
    """
    tid_url = "https://passport.weibo.com/visitor/genvisitor"
    data = {
    "cb": "gen_callback",
    "fp": {
    "os": "3",
    "browser": "Chrome69,0,3497,100",
    "fonts": "undefined",
    "screenInfo": "1920*1080*24",
    "plugins": "Portable Document Format::internal-pdf-viewer::Chrome PDF Plugin|::mhjfbmdgcfjbbpaeojofohoefgiehjai::Chrome PDF Viewer|::internal-nacl-plugin::Native Client"
    }
    }
    req = requests.post(url=tid_url, data=data, headers=headers)

    if req.status_code == 200:
        ret = eval(req.text.replace("window.gen_callback && gen_callback(", "").replace(");", "").replace("true", "1"))
        return ret.get('data').get('tid')
    return None


def get_cookie():
    """
    获取完整的cookie
    :return: cookie
    """
    tid = get_tid()
    print('1')
    if not tid:
        return None
    print('2')
    cookies = {
    "tid": tid + "__095" # + tid_c_w[1]
    }
    url = "https://passport.weibo.com/visitor/visitor?a=incarnate&t={tid}"
    "&w=2&c=095&gc=&cb=cross_domain&from=weibo&_rand={rand}"
    req = requests.get(url.format(tid=tid, rand=random.random()), cookies=cookies, headers=headers)
    if req.status_code != 200:
        return None
    print('3')
    print(req)
    print("--")
    ret = eval(req.text.replace("window.cross_domain && cross_domain(", "").replace(");", "").replace("null", "1"))

    try:
        sub = ret['data']['sub']
        if sub == 1:
            return None
        subp = ret['data']['subp']
    except KeyError:
        return None
    return sub, subp

# if __name__ == "main":
# print(get_cookie())
get_cookie()