"""
    Plugin for ResolveUrl
    Copyright (C) 2020 gujal
    Copyright (C) 2020 groggyegg

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
from net import Net
import common
# import six
# from six.moves import urllib_parse
# from six.moves import urllib_request
# from urlresolver.resolver import ResolverError

try:
    from urllib import quote_plus
except:
    from urllib.parse import quote_plus
"""
from resolveurl import common
from resolveurl.resolver import ResolveUrl, ResolverError
from resolveurl.plugins.lib import helpers
"""


"""
import re
from resolveurl.plugins.lib import helpers
from resolveurl import common
from resolveurl.resolver import ResolveUrl, ResolverError
"""
# https://sbplay2.xyz/e/9htwu7u4btq3
# class StreamSBResolver(ResolveUrl):


class StreamSBResolver():
    name = "streamsb"
    domains = ["sbplay2.xyz", "sbembed.com", "sbembed1.com", "sbplay.org", "sbvideo.net", "streamsb.net", "sbplay.one", "cloudemb.com", "playersb.com", "tubesb.com", "sbplay1.com", "sbfast", "embedsb.com"]
    pattern = r'(?://|\.)((?:tube|player|cloudemb|stream)?s?b?(?:embed\d?|embedsb\d?|play\d?|video)?\.(?:com|net|org|one))/(?:embed-|e|play|d)?/?([0-9a-zA-Z]+)'

    def __init__(self):
        self.net = Net()
#        self.headers = {'User-Agent': common.RAND_UA}
        self.headers = {'User-Agent': common.FF_USER_AGENT}

#    def get_media_url(self, host, media_id):
    def get_media_url(self, url):
        print("streamsb url =", url)
#        host, media_id = self.get_host_and_id(url)
        host = "sbplay2.xyz"
        media_id = "9htwu7u4btq3"
        print("host =", host)
        print("media_id =", media_id)
#        web_url = self.get_url(host, media_id)
#        web_url = 'https://{host}/d/{media_id}.html'
        web_url = 'https://' + host + '/d/' + media_id + ".html"
        headers = {'User-Agent': common.RAND_UA,
                   'Referer': 'https://{0}/'.format(host)}
        html = self.net.http_GET(web_url, headers=headers).content
        sources = re.findall(r'download_video([^"]+)[^\d]+\d+x(\d+)', html)
        if sources:
            sources.sort(key=lambda x: int(x[1]), reverse=True)
            sources = [(x[1] + 'p', x[0]) for x in sources]
            print("streamsb.py sources =", sources)
            # code, mode, hash = eval(helpers.pick_source(sources))
            code, mode, hash = eval(sources[0][1])
            dl_url = 'https://{0}/dl?op=download_orig&id={1}&mode={2}&hash={3}'.format(host, code, mode, hash)
            html = self.net.http_GET(dl_url, headers=headers).content
            r = re.search('href="([^"]+)">Direct', html)
            if r:
                # return r.group(1) + helpers.append_headers(headers)
                return r.group(1)

        raise ResolverError('Video not found')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/d/{media_id}.html')

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
