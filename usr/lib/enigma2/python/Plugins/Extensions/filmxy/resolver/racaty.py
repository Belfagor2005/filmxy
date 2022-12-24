"""
    Plugin for ResolveUrl
    Copyright (C) 2021 shellc0de

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import print_function
import re
from .net import Net
from .common import RAND_UA
try:
    from urllib import quote_plus
except:
    from urllib.parse import quote_plus

from six.moves import urllib_parse, urllib_error
# from urlresolver.resolver import ResolverError
from . import Utils
"""
from resolveurl import common
from resolveurl.lib import helpers
from resolver import ResolveUrl, ResolverError

"""


# from .resolver import ResolveUrl, ResolverError

# class RacatyResolver(ResolveUrl):
    # name = 'Racaty'
    # domains = ['racaty.net', 'racaty.io']
    # pattern = r'(?://|\.)(racaty\.(?:net|io))/(?:embed-)?([0-9a-zA-Z]+)'


# class RacatyResolver(ResolveUrl):
class RacatyResolver():
    name = 'Racaty'
    domains = ['racaty.net', 'racaty.io']
    # domains = ['racaty.io']
    # pattern = r'(?://|\.)(racaty\.net)/([0-9a-zA-Z]+)'
    pattern = r'(?://|\.)(racaty\.(?:net|io))/(?:embed-)?([0-9a-zA-Z]+)'

    def __init__(self):
        # self.net = common.Net(ssl_verify=False)
        self.net = Net()

    # def get_media_url(self, host, media_id):
    def get_media_url(self, url):
        # web_url = self.get_url(host, media_id)
        host, media_id = self.get_host_and_id(url)
        print("host =", host)
        print("media_id =", media_id)
        web_url = "https://" + host + "/" + media_id

        rurl = 'https://{}/'.format(host)
        headers = {
            'Origin': rurl[:-1],
            'Referer': rurl,
            'User-Agent': RAND_UA
            # 'User-Agent': Utils.RequestAgent()
        }
        payload = {
            'op': 'download2',
            'id': media_id,
            'referer': rurl
        }
        html = self.net.http_POST(web_url, form_data=payload, headers=headers).content
        import time
        print("Printed immediately.")
        time.sleep(20.5)
        print('html : ', html)
        try:
            url = re.search(r'id="uniqueExpirylink"\s*href="([^"]+)', html)
            if url:
                headers.update({'verifypeer': 'false'})
                return url.group(1).replace(' ', '%20') + append_headers(headers)
            # return url.group(1).replace(' ', '%20')
            else:
                url = re.search(r'class="downloadbtn"\s*href="([^"]+)', html)
                if url:
                    # headers.update({'verifypeer': 'false'})
                    return url.group(1).replace(' ', '%20') + append_headers(headers)
                    # return url.group(1).replace(' ', '%20')
        except:
            return None
        # if (btn := soup.find(class_="btn btn-dow")): return btn["href"]
        # if (unique := soup.find(id="uniqueExpirylink")): return unique["href"]

    # def append_headers(headers):
        # return '|%s' % '&'.join(['%s=%s' % (key, urllib_parse.quote_plus(headers[key])) for key in headers])

    def get_url(self, host, media_id):
        # return self._default_get_url(host, media_id, template='https://{host}/{media_id}')
        return self._default_get_url(host, media_id, template='https://racaty.io/{media_id}')

    def get_host_and_id(self, url):
        """
        The method that converts a host and media_id into a valid url

        Args:
            url (str): a valid url on the host this resolver resolves

        Returns:
            host (str): the host the link is on
            media_id (str): the media_id the can be returned by get_host_and_id
        """
        r = re.search(self.pattern, url, re.I)
        if r:
            return r.groups()
        else:
            return False


def get_packed_data(html):
    from . import jsunpack  # import *
    packed_data = ''
    for match in re.finditer(r'(eval\s*\(function.*?)</script>', html, re.DOTALL | re.I):
        if jsunpack.detect(match.group(1)):
            packed_data += jsunpack.unpack(match.group(1))
    return packed_data


def append_headers(headers):
    return '|%s' % '&'.join(['%s=%s' % (key, quote_plus(headers[key])) for key in headers])

import requests
from bs4 import BeautifulSoup


"""
https?://(racaty\.net/)\S+
https://racaty.net/10w86dphf8y2
"""

# def racaty_bypass(url):
    # url = url[:-1] if url[-1] == '/' else url
    # token = url.split("/")[-1]

    # client = requests.Session ()
    # headers = {

        # 'content-type': 'application/x-www-form-urlencoded',
        # 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    # }
    # data = {
        # 'op': 'download2',
        # 'id': token,
        # 'rand': '',
        # 'referer': '',
        # 'method_free': '',
        # 'method_premium': '',
    # }
    # response = client.post(url, headers=headers, data=data)
    # soup = BeautifulSoup(response.text, "html.parser")
    # if (btn := soup.find(class_="btn btn-dow")): return btn["href"]
    # if (unique := soup.find(id="uniqueExpirylink")): return unique["href"]

# this Work

def racaty_bypass(url: str) -> str:
    """ Racaty direct link generator
    based on https://github.com/SlamDevs/slam-mirrorbot"""
    dl_url = ''
    try:
        link = re.findall(r'\bhttps?://.*racaty\.net\S+', url)[0]
    except IndexError:
        link = re.findall(r'\bhttps?://.*racaty\.io\S+', url)[0]
        print("No Racaty links found\n")
    from . import cfscrape
    scraper = cfscrape.create_scraper()
    r = scraper.get(url)
    soup = BeautifulSoup(r.text, "lxml")
    op = soup.find("input", {"name": "op"})["value"]
    ids = soup.find("input", {"name": "id"})["value"]
    rpost = scraper.post(url, data = {"op": op, "id": ids})
    rsoup = BeautifulSoup(rpost.text, "lxml")
    dl_url = rsoup.find("a", {"id": "uniqueExpirylink"})["href"].replace(" ", "%20")
    return dl_url
