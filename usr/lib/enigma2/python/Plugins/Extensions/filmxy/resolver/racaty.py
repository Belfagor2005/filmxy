"""
    Plugin for ResolveURL
    Copyright (C) 2021 shellc0de

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
from six.moves import http_cookiejar
import gzip
import re
import json
import six
from six.moves import urllib_request, urllib_parse, urllib_error
import socket
from random import choice
# from . import Utils
# from .net import Net
# from .common import RAND_UA
try:
    from urllib import quote_plus
except:
    from urllib.parse import quote_plus
# from resolveurl import common
# from resolveurl.lib import helpers
# from resolveurl.resolver import ResolveUrl, ResolverError
# import time
# from Plugins.Extensions.WebMedia.Sites.General.Exodus.resolveurl.lib import kodi
# Set Global timeout - Useful for slow connections and Putlocker.
socket.setdefaulttimeout(10)


BR_VERS = [
           ['%s.0' % i for i in range(18, 50)],
           ['37.0.2062.103', '37.0.2062.120', '37.0.2062.124', '38.0.2125.101',
            '38.0.2125.104', '38.0.2125.111', '39.0.2171.71', '39.0.2171.95',
            '39.0.2171.99', '40.0.2214.93', '40.0.2214.111',
            '40.0.2214.115', '42.0.2311.90', '42.0.2311.135', '42.0.2311.152',
            '43.0.2357.81', '43.0.2357.124', '44.0.2403.155', '44.0.2403.157',
            '45.0.2454.101', '45.0.2454.85', '46.0.2490.71',
            '46.0.2490.80', '46.0.2490.86', '47.0.2526.73', '47.0.2526.80',
            '48.0.2564.116', '49.0.2623.112', '50.0.2661.86'],
           ['11.0'],
           ['8.0', '9.0', '10.0', '10.6']]
WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0',
            'Windows NT 6.3', 'Windows NT 6.2',
            'Windows NT 6.1', 'Windows NT 6.0',
            'Windows NT 5.1', 'Windows NT 5.0']
FEATURES = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
RAND_UAS = ['Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
            'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
            'Mozilla/5.0 ({win_ver}{feature}; Trident/7.0; rv:{br_ver}) like Gecko',
            'Mozilla/5.0 (compatible; MSIE {br_ver}; {win_ver}{feature}; Trident/6.0)']


# Supported video formats
VIDEO_FORMATS = ['.aac', '.asf', '.avi', '.flv', '.m4a', '.m4v', '.mka', '.mkv', '.mp4', '.mpeg', '.nut', '.ogg']


# RAND_UA = get_ua()
IE_USER_AGENT = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
FF_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'
OPERA_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36 OPR/67.0.3575.97'
IOS_USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Safari/604.1'
ANDROID_USER_AGENT = 'Mozilla/5.0 (Linux; Android 9; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Mobile Safari/537.36'
EDGE_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363'
CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4136.7 Safari/537.36'
SAFARI_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15'
# SMR_USER_AGENT = 'ResolveURL for Kodi/%s' % (addon_version)


# Quick hack till I decide how to handle this
_USER_AGENTS = [FF_USER_AGENT, OPERA_USER_AGENT, EDGE_USER_AGENT, CHROME_USER_AGENT, SAFARI_USER_AGENT]
RAND_UA = choice(_USER_AGENTS)


def get_ua():
    """
    try:
        last_gen = int(kodi.get_setting('last_ua_create'))
    except:
        last_gen = 0
    if not kodi.get_setting('current_ua') or last_gen < (time.time() - (7 * 24 * 60 * 60)):
        index = random.randrange(len(RAND_UAS))
        versions = {'win_ver': random.choice(WIN_VERS), 'feature': random.choice(FEATURES), 'br_ver': random.choice(BR_VERS[index])}
        user_agent = RAND_UAS[index].format(**versions)
        # logger.log('Creating New User Agent: %s' % (user_agent), log_utils.LOGDEBUG)
        kodi.set_setting('current_ua', user_agent)
        kodi.set_setting('last_ua_create', str(int(time.time())))
    else:
        user_agent = kodi.get_setting('current_ua')
    return user_agent
    """
    pass


class Net:
    """
    This class wraps :mod:`urllib2` and provides an easy way to make http
    requests while taking care of cookies, proxies, gzip compression and
    character encoding.

    Example::

        from addon.common.net import Net
        net = Net()
        response = net.http_GET('http://xbmc.org')
        print response.content
    """

    _cj = http_cookiejar.LWPCookieJar()
    _proxy = None
    _user_agent = 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0'
    _http_debug = False

    def __init__(self, cookie_file='', proxy='', user_agent='', ssl_verify=True, http_debug=False):
        """
        Kwargs:
            cookie_file (str): Full path to a file to be used to load and save
            cookies to.

            proxy (str): Proxy setting (eg.
            ``'http://user:pass@example.com:1234'``)

            user_agent (str): String to use as the User Agent header. If not
            supplied the class will use a default user agent (chrome)

            http_debug (bool): Set ``True`` to have HTTP header info written to
            the XBMC log for all requests.
        """
        if cookie_file:
            self.set_cookies(cookie_file)
        if proxy:
            self.set_proxy(proxy)
        if user_agent:
            self.set_user_agent(user_agent)
        self._ssl_verify = ssl_verify
        self._http_debug = http_debug
        self._update_opener()

    def set_cookies(self, cookie_file):
        """
        Set the cookie file and try to load cookies from it if it exists.

        Args:
            cookie_file (str): Full path to a file to be used to load and save
            cookies to.
        """
        try:
            self._cj.load(cookie_file, ignore_discard=True)
            self._update_opener()
            return True
        except:
            return False

    def get_cookies(self, as_dict=False):
        """Returns A dictionary containing all cookie information by domain."""
        if as_dict:
            return dict((cookie.name, cookie.value) for cookie in self._cj)
        else:
            return self._cj._cookies

    def save_cookies(self, cookie_file):
        """
        Saves cookies to a file.

        Args:
            cookie_file (str): Full path to a file to save cookies to.
        """
        self._cj.save(cookie_file, ignore_discard=True)

    def set_proxy(self, proxy):
        """
        Args:
            proxy (str): Proxy setting (eg.
            ``'http://user:pass@example.com:1234'``)
        """
        self._proxy = proxy
        self._update_opener()

    def get_proxy(self):
        """Returns string containing proxy details."""
        return self._proxy

    def set_user_agent(self, user_agent):
        """
        Args:
            user_agent (str): String to use as the User Agent header.
        """
        self._user_agent = user_agent

    def get_user_agent(self):
        """Returns user agent string."""
        return self._user_agent

    def _update_opener(self, drop_tls_level=False):
        """
        Builds and installs a new opener to be used by all future calls to
        :func:`urllib2.urlopen`.
        """
        handlers = [urllib_request.HTTPCookieProcessor(self._cj), urllib_request.HTTPBasicAuthHandler()]

        if self._http_debug:
            handlers += [urllib_request.HTTPHandler(debuglevel=1)]
        else:
            handlers += [urllib_request.HTTPHandler()]

        if self._proxy:
            handlers += [urllib_request.ProxyHandler({'http': self._proxy})]

        try:
            import platform
            node = platform.node().lower()
        except:
            node = ''

        if not self._ssl_verify or node == 'xboxone':
            try:
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                if self._http_debug:
                    handlers += [urllib_request.HTTPSHandler(context=ctx, debuglevel=1)]
                else:
                    handlers += [urllib_request.HTTPSHandler(context=ctx)]
            except:
                pass

        if drop_tls_level:
            try:
                import ssl
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_1)
                if self._http_debug:
                    handlers += [urllib_request.HTTPSHandler(context=ctx, debuglevel=1)]
                else:
                    handlers += [urllib_request.HTTPSHandler(context=ctx)]
            except:
                pass

        opener = urllib_request.build_opener(*handlers)
        urllib_request.install_opener(opener)

    def http_GET(self, url, headers={}, compression=True):
        """
        Perform an HTTP GET request.

        Args:
            url (str): The URL to GET.

        Kwargs:
            headers (dict): A dictionary describing any headers you would like
            to add to the request. (eg. ``{'X-Test': 'testing'}``)

            compression (bool): If ``True`` (default), try to use gzip
            compression.

        Returns:
            An :class:`HttpResponse` object containing headers and other
            meta-information about the page and the page content.
        """
        return self._fetch(url, headers=headers, compression=compression)

    def http_POST(self, url, form_data, headers={}, compression=True, jdata=False):
        """
        Perform an HTTP POST request.

        Args:
            url (str): The URL to POST.

            form_data (dict): A dictionary of form data to POST.

        Kwargs:
            headers (dict): A dictionary describing any headers you would like
            to add to the request. (eg. ``{'X-Test': 'testing'}``)

            compression (bool): If ``True`` (default), try to use gzip
            compression.

        Returns:
            An :class:`HttpResponse` object containing headers and other
            meta-information about the page and the page content.
        """
        return self._fetch(url, form_data, headers=headers, compression=compression, jdata=jdata)

    def http_HEAD(self, url, headers={}):
        """
        Perform an HTTP HEAD request.

        Args:
            url (str): The URL to GET.

        Kwargs:
            headers (dict): A dictionary describing any headers you would like
            to add to the request. (eg. ``{'X-Test': 'testing'}``)

        Returns:
            An :class:`HttpResponse` object containing headers and other
            meta-information about the page.
        """
        request = urllib_request.Request(url)
        request.get_method = lambda: 'HEAD'
        request.add_header('User-Agent', self._user_agent)
        for key in headers:
            request.add_header(key, headers[key])
        response = urllib_request.urlopen(request)
        return HttpResponse(response)

    def http_DELETE(self, url, headers={}):
        """
        Perform an HTTP DELETE request.

        Args:
            url (str): The URL to GET.

        Kwargs:
            headers (dict): A dictionary describing any headers you would like
            to add to the request. (eg. ``{'X-Test': 'testing'}``)

        Returns:
            An :class:`HttpResponse` object containing headers and other
            meta-information about the page.
        """
        request = urllib_request.Request(url)
        request.get_method = lambda: 'DELETE'
        request.add_header('User-Agent', self._user_agent)
        for key in headers:
            request.add_header(key, headers[key])
        response = urllib_request.urlopen(request)
        return HttpResponse(response)

    def _fetch(self, url, form_data={}, headers={}, compression=True, jdata=False):
        """
        Perform an HTTP GET or POST request.

        Args:
            url (str): The URL to GET or POST.

            form_data (dict): A dictionary of form data to POST. If empty, the
            request will be a GET, if it contains form data it will be a POST.

        Kwargs:
            headers (dict): A dictionary describing any headers you would like
            to add to the request. (eg. ``{'X-Test': 'testing'}``)

            compression (bool): If ``True`` (default), try to use gzip
            compression.

        Returns:
            An :class:`HttpResponse` object containing headers and other
            meta-information about the page and the page content.
        """
        req = urllib_request.Request(url)
        if form_data:
            if jdata:
                form_data = json.dumps(form_data)
            elif isinstance(form_data, six.string_types):
                form_data = form_data
            else:
                form_data = urllib_parse.urlencode(form_data, True)
            form_data = form_data.encode('utf-8') if six.PY3 else form_data
            req = urllib_request.Request(url, form_data)
        req.add_header('User-Agent', self._user_agent)
        for key in headers:
            req.add_header(key, headers[key])
        if compression:
            req.add_header('Accept-Encoding', 'gzip')
        if jdata:
            req.add_header('Content-Type', 'application/json')
        host = req.host if six.PY3 else req.get_host()
        req.add_unredirected_header('Host', host)
        try:
            response = urllib_request.urlopen(req, timeout=15)
        except urllib_error.HTTPError as e:
            if e.code == 403:
                self._update_opener(drop_tls_level=True)
            response = urllib_request.urlopen(req, timeout=15)

        return HttpResponse(response)


class HttpResponse:
    """
    This class represents a resoponse from an HTTP request.

    The content is examined and every attempt is made to properly decode it to
    Unicode unless the nodecode property flag is set to True.

    .. seealso::
        :meth:`Net.http_GET`, :meth:`Net.http_HEAD` and :meth:`Net.http_POST`
    """

    # content = ''
    """Unicode encoded string containing the body of the reponse."""

    def __init__(self, response):
        """
        Args:
            response (:class:`mimetools.Message`): The object returned by a call
            to :func:`urllib2.urlopen`.
        """
        self._response = response
        self._nodecode = False

    @property
    def content(self):
        html = self._response.read()
        encoding = None
        try:
            if self._response.headers['content-encoding'].lower() == 'gzip':
                html = gzip.GzipFile(fileobj=six.BytesIO(html)).read()
        except:
            pass

        if self._nodecode:
            return html

        try:
            content_type = self._response.headers['content-type']
            if 'charset=' in content_type:
                encoding = content_type.split('charset=')[-1]
        except:
            pass

        if encoding is None:
            epattern = r'<meta\s+http-equiv="Content-Type"\s+content="(?:.+?);\s+charset=(.+?)"'
            epattern = epattern.encode('utf8') if six.PY3 else epattern
            r = re.search(epattern, html, re.IGNORECASE)
            if r:
                encoding = r.group(1).decode('utf8') if six.PY3 else r.group(1)

        if encoding is not None:
            html = html.decode(encoding, errors='ignore')
        else:
            html = html.decode('ascii', errors='ignore') if six.PY3 else html
        return html

    def get_headers(self, as_dict=False):
        """Returns headers returned by the server.
        If as_dict is True, headers are returned as a dictionary otherwise a list"""
        if as_dict:
            hdrs = {}
            for item in list(self._response.info().items()):
                if item[0].title() not in list(hdrs.keys()):
                    hdrs.update({item[0].title(): item[1]})
                else:
                    hdrs.update({item[0].title(): ','.join([hdrs[item[0].title()], item[1]])})
            # return dict([(item[0].title(), item[1]) for item in list(self._response.info().items())])
            return hdrs
        else:
            return self._response.info()._headers if six.PY3 else [(x.split(':')[0].strip(), x.split(':')[1].strip()) for x in self._response.info().headers]

    def get_url(self):
        """
        Return the URL of the resource retrieved, commonly used to determine if
        a redirect was followed.
        """
        return self._response.geturl()

    def nodecode(self, nodecode):
        """
        Sets whether or not content returns decoded text
        nodecode (bool): Set to ``True`` to allow content to return undecoded data
        suitable to write to a binary file
        """
        self._nodecode = bool(nodecode)
        return self


# class RacatyResolver(ResolveUrl):
class RacatyResolver():
    name = 'Racaty'
    domains = ['racaty.io', 'racaty.net']
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
        print("web_url =", web_url)
        
        rurl = 'https://{}/'.format(host)
        headers = {
            'Origin': rurl[:-1],
            'Referer': rurl,
            'User-Agent': RAND_UA
        }
        payload = {
            'op': 'download2',
            'id': media_id,
            'referer': rurl
        }
        html = self.net.http_POST(web_url, form_data=payload, headers=headers).content
        import time
        print("Printed html immediately.")
        time.sleep(12.0)
        print('html: ', html)

        try:
            url = re.search(r'id="uniqueExpirylink"\s*href="([^"]+)', html)
            if url:
                headers.update({'verifypeer': 'false'})
                return url.group(1) + append_headers(headers)
            # # return url.group(1).replace(' ', '%20')
            else:
                url = re.search(r'class="downloadbtn"\s*href="([^"]+)', html)
                if url:
                    # headers.update({'verifypeer': 'false'})
                    return url.group(1) + append_headers(headers)
                    # return url.group(1).replace(' ', '%20')
        except:
            return None


    def get_url(self, host, media_id):
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
            print('re.search.groups() ', r.groups())
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
