# -*- coding: utf-8 -*-


# import urllib2

import sys

PY3 = sys.version_info[0] == 3
if PY3:
    from urllib.request import urlopen, Request
else:
    from urllib2 import urlopen, Request


def getUrl(url):
    pass  # print "Here in client2 getUrl url =", url
    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urlopen(req)
    link = response.read()
    response.close()
    return link


def getUrl2(url, referer):
    pass  # print "Here in client2 getUrl2 url =", url
    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    req.add_header('Referer', referer)
    response = urlopen(req)
    link = response.read()
    response.close()
    return link
