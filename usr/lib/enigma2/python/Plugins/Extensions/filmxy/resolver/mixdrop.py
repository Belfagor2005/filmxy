"""
    Plugin for ResolveURL
    Copyright (C) 2019 gujal

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import print_function
import re
# import six
from six.moves import urllib_parse
# from six.moves import urllib_request
# from urlresolver.resolver import ResolverError
import jsunpack
from net import Net
import common


# class MixdropResolver(ResolveUrl):

class MixdropResolver():
    name = "mixdrop"
    domains = ["mixdrop.co", "mixdrop.to", "mixdrop.sx"]
    pattern = r'(?://|\.)(mixdrop\.(?:co|to|sx))/(?:f|e)/(\w+)'

    def __init__(self):
        self.net = Net()
        # self.headers = {'User-Agent': common.RAND_UA}
        self.headers = {'User-Agent': common.FF_USER_AGENT}

    # def get_media_url(self, host, media_id):
    def get_media_url(self, url):
        host, media_id = self.get_host_and_id(url)
        print("host =", host)
        print("media_id =", media_id)
        # web_url = self.get_url(host, media_id)
        web_url = 'https://' + host + '/e/' + media_id
        headers = {'Origin': 'https://{}'.format(host),
                   'Referer': 'https://{}/'.format(host),
                   'User-Agent': common.RAND_UA}
        html = self.net.http_GET(web_url, headers=headers).content
        print("mixdrop html =", html)
        r = re.search(r'location\s*=\s*"([^"]+)', html)
        print("mixdrop r =", r)
        if r:
            web_url = 'https://{0}{1}'.format(host, r.group(1))
            html = self.net.http_GET(web_url, headers=headers).content
        if '(p,a,c,k,e,d)' in html:
            # html = helpers.get_packed_data(html)
            html = get_packed_data(html)
            print("mixdrop html 2 =", html)
        r = re.search(r'(?:vsr|wurl|surl)[^=]*=\s*"([^"]+)', html)
        if r:
            headers = {'User-Agent': common.RAND_UA, 'Referer': web_url}
            # return "https:" + r.group(1) + helpers.append_headers(headers)
            # return "https:" + r.group(1) + append_headers(headers)
            return "https:" + r.group(1)
        raise ResolverError("Video not found")

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/e/{media_id}')

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
    packed_data = ''
    for match in re.finditer(r'(eval\s*\(function.*?)</script>', html, re.DOTALL | re.I):
        if jsunpack.detect(match.group(1)):
            packed_data += jsunpack.unpack(match.group(1))
    return packed_data


def append_headers(headers):
    return '|%s' % '&'.join(['%s=%s' % (key, urllib_parse.quote_plus(headers[key])) for key in headers])
