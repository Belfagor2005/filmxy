#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*        Many thank's Pcd              *
*             06/07/2023               *
*       skin by MMark                  *
****************************************
Info http://t.me/tivustream
'''
from __future__ import print_function
from . import Utils
from . import html_conv
from . import _, paypal
try:
    from Components.AVSwitch import eAVSwitch
except Exception:
    from Components.AVSwitch import iAVSwitch as eAVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText
from Components.Task import Task, Condition, Job, job_manager
from Components.config import ConfigDirectory, ConfigSubsection
from Components.config import ConfigYesNo, ConfigSelection
from Components.config import config, ConfigEnableDisable
from Components.config import ConfigOnOff
from Components.config import getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBarGenerics import InfoBarNotifications
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarAudioSelection
from Screens.InfoBarGenerics import InfoBarSubtitleSupport, InfoBarMenu
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.TaskView import JobView
from Tools.Directories import SCOPE_PLUGINS
from Tools.Directories import resolveFilename, fileExists
from Tools.Downloader import downloadWithProgress
from .Downloader import DownloadWithProgress
from enigma import RT_VALIGN_CENTER
from enigma import RT_HALIGN_LEFT
from enigma import eListboxPythonMultiContent
from enigma import ePicLoad, loadPNG
from enigma import gFont, gPixmapPtr
from enigma import eServiceReference
from enigma import eTimer
from enigma import iPlayableService
from enigma import getDesktop
from os.path import splitext
from twisted.web.client import downloadPage
import os
import requests
import re
import six
import ssl
import sys
import time
from requests import get, exceptions
from requests.exceptions import HTTPError
from twisted.internet.reactor import callInThread
PY3 = False
PY3 = sys.version_info.major >= 3
print('Py3: ', PY3)


def trace_error():
    import traceback
    try:
        traceback.print_exc(file=sys.stdout)
        traceback.print_exc(file=open('/tmp/traceback.log', 'a'))
    except:
        pass


def logdata(name='', data=None):
    try:
        data = str(data)
        fp = open('/tmp/filmxy.log', 'a')
        fp.write(str(name) + ': ' + data + "\n")
        fp.close()
    except:
        trace_error()
        pass


def clear_caches():
    try:
        os.system("echo 1 > /proc/sys/vm/drop_caches")
        os.system("echo 2 > /proc/sys/vm/drop_caches")
        os.system("echo 3 > /proc/sys/vm/drop_caches")
    except:
        pass


if PY3:
    logdata('PY3: True ')


try:
    from urllib.parse import urlparse, unquote
    from urllib.request import urlretrieve, urlopen
    from urllib.request import Request
    from urllib.error import URLError
    PY3 = True
    unicode = str
    unichr = chr
    long = int
except ImportError:
    from urlparse import urlparse
    from urllib import urlretrieve
    from urllib2 import Request
    from urllib import unquote
    from urllib2 import urlopen
    from urllib2 import URLError

if PY3:
    print('six.PY3: True ')

plugin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('filmxy'))
global skin_path, nextmodule, Path_Movies

_session = None
_firstStart = True
# Host = "http://www.filmxy.pw/"
Host = "https://www.filmxy.online/"
referer = "http://www.filmxy.online"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'Accept-Encoding': 'deflate'}

streamlink = False
if Utils.isStreamlinkAvailable:
    streamlink = True


try:
    from Plugins.Extensions.SubsSupport import SubsSupport, SubsSupportStatus
except ImportError:
    class SubsSupport(object):

        def __init__(self, *args, **kwargs):
            pass


class SubsSupportStatus(object):
    def __init__(self, *args, **kwargs):
        pass


def cleantitle(title):
    cleanName = re.sub(r'[\<\>\:\"\/\\\|\?\*\(\)\[\]]', " ", str(title))
    cleanName = re.sub(r"  ", " ", cleanName)
    cleanName = cleanName.strip()
    return cleanName


def getversioninfo():
    currversion = '1.3'
    version_file = os.path.join(plugin_path, '/version')
    if os.path.exists(version_file):
        try:
            fp = open(version_file, 'r').readlines()
            for line in fp:
                if 'version' in line:
                    currversion = line.split('=')[1].strip()
        except:
            pass
    logdata("Plugin ", plugin_path)
    logdata("Version ", currversion)
    return (currversion)


try:
    from twisted.internet import ssl
    from twisted.internet._sslverify import ClientTLSOptions
    sslverify = True
except:
    sslverify = False

if sslverify:
    class SNIFactory(ssl.ClientContextFactory):
        def __init__(self, hostname=None):
            self.hostname = hostname

        def getContext(self):
            ctx = self._contextFactory(self.method)
            if self.hostname:
                ClientTLSOptions(self.hostname, ctx)
            return ctx


modechoices = [
               ("4097", _("ServiceMp3(4097)")),
               ("1", _("Hardware(1)")),
              ]

if os.path.exists("/usr/bin/gstplayer"):
    modechoices.append(("5001", _("Gstreamer(5001)")))
if os.path.exists("/usr/bin/exteplayer3"):
    modechoices.append(("5002", _("Exteplayer3(5002)")))
if os.path.exists("/usr/sbin/streamlinksrv"):
    modechoices.append(("5002", _("Streamlink(5002)")))
if os.path.exists("/usr/bin/apt-get"):
    modechoices.append(("8193", _("eServiceUri(8193)")))

config.plugins.filmxy = ConfigSubsection()
config.plugins.filmxy.cachefold = ConfigDirectory(default='/media/hdd/filmxy/')
config.plugins.filmxy.movie = ConfigDirectory("/media/hdd/movie")
try:
    from Components.UsageConfig import defaultMoviePath
    downloadpath = defaultMoviePath()
    config.plugins.filmxy.movie = ConfigDirectory(default=downloadpath)
except:
    if os.path.exists("/usr/bin/apt-get"):
        config.plugins.filmxy.movie = ConfigDirectory(default='/media/hdd/movie/')
config.plugins.filmxy.services = ConfigSelection(default='4097', choices=modechoices)

config.plugins.filmxy.servicesforce = ConfigOnOff(default=False)
cfg = config.plugins.filmxy

currversion = getversioninfo()
title_plug = 'Filmxy V. %s' % currversion
desc_plug = 'Filmxy'
ico_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/logo.png".format('filmxy'))
res_plugin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/".format('filmxy'))
piccons = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/img/".format('filmxy'))
no_cover = piccons + 'no_cover.png'
piconmovie = piccons + 'cinema.png'
piconseries = piccons + 'series.png'
piconsearch = piccons + 'search.png'
piconinter = piccons + 'inter.png'
pixmaps = piccons + 'null.png'
piconold = piccons + 'vecchi.png'
nextpng = 'next.png'
prevpng = 'prev.png'
Path_Tmp = "/tmp"
Path_Movies = str(config.plugins.filmxy.movie.value)
cachefold = config.plugins.filmxy.cachefold.value.strip()
pictmp = cachefold + "poster.jpg"
print('patch movies: ', Path_Movies)
pmovies = False
status = False
ui = False

if not os.path.exists(cachefold):
    try:
        os.makedirs(cachefold)
    except OSError as e:
        logdata(('Error creating directory %s:\n%s') % (cachefold, e))


screenwidth = getDesktop(0).size()
if screenwidth.width() == 2560:
    skin_path = plugin_path + '/res/skins/uhd/'
elif screenwidth.width() == 1920:
    skin_path = plugin_path + '/res/skins/fhd/'
else:
    skin_path = plugin_path + '/res/skins/hd/'

if Utils.DreamOS():
    skin_path = skin_path + 'dreamOs/'
logdata("path skin_path: ", str(skin_path))


def returnIMDB(text_clear):
    TMDB = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('TMDB'))
    IMDb = resolveFilename(SCOPE_PLUGINS, "Extensions/{}".format('IMDb'))
    if os.path.exists(TMDB):
        try:
            from Plugins.Extensions.TMBD.plugin import TMBD
            text = html_conv.html_unescape(text_clear)
            _session.open(TMBD.tmdbScreen, text, 0)
        except Exception as e:
            print("[XCF] Tmdb: ", e)
        return True
    elif os.path.exists(IMDb):
        try:
            from Plugins.Extensions.IMDb.plugin import main as imdb
            text = html_conv.html_unescape(text_clear)
            imdb(_session, text)
        except Exception as e:
            print("[XCF] imdb: ", e)
        return True
    else:
        text_clear = html_conv.html_unescape(text_clear)
        _session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)
        return True
    return False


def status_site():
    global status
    url = Host
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        status = True
        print('Web site exists')
    else:
        status = False
        print('Web site does not exist')
    return status


def piconlocal(name):

    pngs = [
        ["tv", "movie"],
        ["commedia", "commedia"],
        ["comedy", "commedia"],
        ["thriller", "thriller"],
        ["family", "family"],
        ["azione", "azione"],
        ["dramma", "dramma"],
        ["drama", "dramma"],
        ["western", "western"],
        ["biografico", "biografico"],
        ["storia", "biografico"],
        ["documentario", "biografico"],
        ["romantico", "romantico"],
        ["romance", "romantico"],
        ["horror", "horror"],
        ["musica", "musical"],
        ["show", "musical"],
        ["guerra", "guerra"],
        ["bambini", "bambini"],
        ["bianco", "bianconero"],
        ["tutto", "toto"],
        ["cartoni", "cartoni"],
        ["bud", "budterence"],
        ["documentary", "documentary"],
        ["crime", "crime"],
        ["mystery", "mistery"],
        ["mistero", "mistery"],
        ["giallo", "mistery"],
        ["fiction", "fiction"],
        ["adventure", "mistery"],
        ["action", "azione"],
        ["007", "007"],
        ["sport", "sport"],
        ["teatr", "teatro"],
        ["variet", "teatro"],
        ["giallo", "teatro"],
        ["extra", "extra"],
        ["sexy", "fantasy"],
        ["erotic", "fantasy"],
        ["animazione", "bambini"],
        ["search", "search"],
        ["abruzzo", "regioni/abruzzo"],
        ["basilicata", "regioni/basilicata"],
        ["calabria", "regioni/calabria"],
        ["campania", "regioni/campania"],
        ["emilia", "regioni/emiliaromagna"],
        ["friuli", "regioni/friuliveneziagiulia"],
        ["lazio", "regioni/lazio"],
        ["liguria", "regioni/liguria"],
        ["lombardia", "regioni/lombardia"],
        ["marche", "regioni/marche"],
        ["molise", "regioni/molise"],
        ["piemonte", "regioni/piemonte"],
        ["puglia", "regioni/puglia"],
        ["sardegna", "regioni/sardegna"],
        ["sicilia", "regioni/sicilia"],
        ["toscana", "regioni/toscana"],
        ["trentino", "regioni/trentino"],
        ["umbria", "regioni/umbria"],
        ["veneto", "regioni/veneto"],
        ["aosta", "regioni/valledaosta"],
        ["mediaset", "mediaset"],
        ["nazionali", "nazionali"],
        ["news", "news"],
        ["rai", "rai"],
        ["webcam", "relaxweb"],
        ["relax", "relaxweb"],
        ["vecchi", "vecchi"],
        ["muto", "vecchi"],
        ["'italiani", "movie"],
        ["fantascienza", "fantascienza"],
        ["fantasy", "fantasy"],
        ["fantasia", "fantasia"],
        ["film", "movie"],
        ["samsung", "samsung"],
        ["plutotv", "plutotv"]
    ]

    for png in pngs:
        piconlocal = 'backg.png'
        if png[0] in str(name).lower():
            piconlocal = str(png[1]) + ".png"
            break

    if 'prev' in name.lower():
        piconlocal = prevpng
    elif 'next' in name.lower():
        piconlocal = nextpng
    path = plugin_path + '/res/img/' + piconlocal
    print('>>>>>>>> ' + path)
    return str(path)


EXTRAD = "radio", "radyo", "mix", "fm", "kbit", "rap", "metal", "alternative"
EXTXXX = "adult", "xxx"
EXTCAM = "webcam", "webcams"
EXTMUS = "music", "mtv", "deluxe", "djing", "fashion", "kiss", "mpeg", "sluhay", "stingray", "techno", "viva", "country", "vevo"
EXTSPOR = "sport", "boxing", "racing", "fight", "golf", "knock", "harley", "futbool", "motor", "nba", "nfl", "bull", "poker", "billiar", "fite"
EXTRLX = "relax", "nature", "escape"
EXTMOV = "movie", "film"
EXTWEA = "weather"
EXTFAM = "family"
EXTREL = "religious"
EXTSHP = "shop"
EXTTRV = "travel"

EXTDOWN = {
        ".avi": "movie",
        ".divx": "movie",
        ".mpg": "movie",
        ".mpeg": "movie",
        ".mkv": "movie",
        ".mov": "movie",
        ".m4v": "movie",
        ".flv": "movie",
        ".m3u8": "movie",
        ".relinker": "movie",
        ".mp4": "movie",
    }


class rvList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if screenwidth.width() == 2560:
            self.l.setItemHeight(60)
            textfont = int(42)
            self.l.setFont(0, gFont('Regular', textfont))
        elif screenwidth.width() == 1920:
            self.l.setItemHeight(50)
            textfont = int(30)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(50)
            textfont = int(24)
            self.l.setFont(0, gFont('Regular', textfont))


def rvListEntry(name, idx):
    name = Utils.checkStr(name)
    res = [name]
    if 'radio' in name.lower():
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/radio.png".format('filmxy'))
    elif 'webcam' in name.lower():
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/webcam.png".format('filmxy'))
    elif 'music' in name.lower():
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/music.png".format('filmxy'))
    elif 'sport' in name.lower():
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/sport.png".format('filmxy'))
    else:
        pngs = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/pics/tv.png".format('filmxy'))

    if screenwidth.width() == 2560:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 2), size=(55, 55), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(80, 0), size=(1200, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    elif screenwidth.width() == 1920:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 5), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(70, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(3, 3), size=(40, 40), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(50, 0), size=(500, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    return res


def showlist(data, list):
    idx = 0
    plist = []
    for line in data:
        name = data[idx]
        plist.append(rvListEntry(name, idx))
        idx = idx + 1
        list.setList(plist)


PanelMain = [
             ('A-Z'),
             ('CATEGORIES'),
             ('COUNTRIES'),
             ('YEARS')]


class Filmxymain(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        global _session, nextmodule
        _session = session
        nextmodule = 'Filmxymain'
        skin = os.path.join(skin_path, 'Filmxymain.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME FILMXY')
        self['list'] = rvList([])
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + cachefold)
        self['poster'] = Pixmap()
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('SERVER STATUS')
        self['desc'] = StaticText()
        self['descadd'] = Label('Press Menu for Coffe')
        self['info'] = Label('')
        self['info'].setText('Select')
        self['key_red'] = Button(_('Exit'))
        self.currentList = 'list'
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.idx = 0
        self.menulist = []
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['DirectionActions',
                                     'OkCancelActions',
                                     'EPGSelectActions',
                                     'ColorActions',
                                     'ButtonSetupActions',
                                     'MenuActions'], {'ok': self.okRun,
                                                      'green': self.okRun,
                                                      'back': self.closerm,
                                                      'red': self.closerm,
                                                      # 'yellow': self.remove,
                                                      # 'blue': self.msgtqm,
                                                      'epg': self.showIMDB,
                                                      'info': self.showIMDB,
                                                      'up': self.up,
                                                      'down': self.down,
                                                      'left': self.left,
                                                      'right': self.right,
                                                      'menu': self.goConfig,
                                                      'cancel': self.closerm}, -1)

        self.onLayoutFinish.append(self.updateMenuList)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        try:
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                print('show imdb/tmdb')
        except Exception as e:
            print('error showIMDB ', e)

    def __layoutFinished(self):
        status = status_site()
        if status is True:
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(self.setup_title)
        # self.load_infos()
        self.load_poster()

    def closerm(self):
        self.close()

    def updateMenuList(self):
        self.menu_list = []
        for x in self.menu_list:
            del self.menu_list[0]
        list = []
        self.idx = 0
        for x in PanelMain:
            list.append(rvListEntry(x, self.idx))
            self.menu_list.append(x)
            self.idx += 1
        self['list'].setList(list)
        self.load_poster()

    def okRun(self):
        self.keyNumberGlobalCB(self['list'].getSelectedIndex())

    def keyNumberGlobalCB(self, idx):
        i = len(self.menu_list)
        if i < 0:
            return
        # if status is True:
        global nextmodule
        sel = self.menu_list[idx]
        if sel == ('CATEGORIES'):
            name = 'CATEGORIES'
            url = Host
            pic = piconmovie
            nextmodule = name.lower()
            self.session.open(live_to_stream, name, url, pic, nextmodule)
        elif sel == ('COUNTRIES'):
            name = 'COUNTRIES'
            url = Host
            pic = piconinter
            nextmodule = name.lower()
            self.session.open(live_to_stream, name, url, pic, nextmodule)
        elif sel == 'YEARS':
            name = 'YEARS'
            url = Host
            pic = piconold
            nextmodule = name.lower()
            self.session.open(live_to_stream, name, url, pic, nextmodule)
        elif sel == ('A-Z'):
            name = 'A-Z'
            url = Host
            pic = piconsearch
            nextmodule = name.lower()
            self.session.open(live_to_stream, name, url, pic, nextmodule)
        else:
            if sel == ('INTERNATIONAL'):
                self.zfreearhey()
        logdata("Filmxymain nextmodule: ", nextmodule)

    def zfreearhey(self):
        freearhey = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/skin".format('freearhey'))
        if os.path.isdir(freearhey):
            from Plugins.Extensions.freearhey.plugin import freearhey
            self.session.open(freearhey)
        else:
            try:
                self.mbox = self.session.open(MessageBox, _('freearhey Plugin Not Installed!!\nUse my Plugin Freearhey'), MessageBox.TYPE_INFO, timeout=4)
            except Exception as e:
                print('error infobox ', e)

    def goConfig(self):
        self.session.open(myconfig)

    def up(self):
        self[self.currentList].up()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_poster()

    def load_poster(self):
        try:
            idx = self['list'].getSelectedIndex()
            sel = self.menu_list[idx]
            if sel is not None or sel != -1:
                if sel == ('CATEGORIES'):
                    pixmaps = piconmovie
                elif sel == ('COUNTRIES'):
                    pixmaps = piconinter
                elif sel == ('YEARS'):
                    pixmaps = piconold
                elif sel == ('A-Z'):
                    pixmaps = piconsearch
                else:
                    pixmaps = piconmovie
                size = self['poster'].instance.size()
                if Utils.DreamOS():
                    self['poster'].instance.setPixmap(gPixmapPtr())
                else:
                    self['poster'].instance.setPixmap(None)
                self.scale = eAVSwitch().getFramebufferScale()
                self.picload = ePicLoad()
                self.picload.setPara((size.width(),
                                      size.height(),
                                      self.scale[0],
                                      self.scale[1],
                                      False,
                                      1,
                                      '#FF000000'))
                ptr = self.picload.getData()
                if Utils.DreamOS():
                    if self.picload.startDecode(pixmaps, False) == 0:
                        ptr = self.picload.getData()
                else:
                    if self.picload.startDecode(pixmaps, 0, 0, False) == 0:
                        ptr = self.picload.getData()
                if ptr is not None:
                    self['poster'].instance.setPixmap(ptr)
                    self['poster'].show()
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in Playchoice")
        return


class live_to_stream(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(skin_path, 'Filmxymain.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME FILMXY')
        self.setTitle(title_plug)
        self.list = []
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + cachefold)
        self['desc'] = StaticText()
        self['descadd'] = Label(_('Select your %s') % nextmodule)
        self["poster"] = Pixmap()
        self['statusgreen'] = Pixmap()
        self['statusred'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'].hide()
        self['status'] = Label('SERVER STATUS')
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.desc = nextmodule
        self.type = self.name
        self.downloading = False
        self.currentList = 'list'
        self.idx = 0
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['DirectionActions',
                                     'OkCancelActions',
                                     'EPGSelectActions',
                                     'ButtonSetupActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'red': self.cancel,
                                                       'up': self.up,
                                                       'down': self.down,
                                                       'left': self.left,
                                                       'right': self.right,
                                                       'epg': self.showIMDB,
                                                       'info': self.showIMDB,
                                                       'cancel': self.cancel}, -2)

        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(300, True)
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.left)
        except:
            self.leftt.callback.append(self.left)
        self.leftt.start(500, True)
        self.onLayoutFinish.append(self.__layoutFinished)
        # self.currentList.moveToIndex(0)

    def showIMDB(self):
        try:
            i = len(self.names)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                logdata("show imdb/tmdb ", text_clear)
        except Exception as e:
            print(e)
            print("Error: can't find showIMDB in live_to_stream")

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        try:
            if 'categories' in self.desc.lower():
                content = Utils.ReadUrl2(Host, referer)
                n1 = content.find("var genre=", 0)
                n2 = content.find("var years=", n1)
                content2 = content[n1:n2]
                regexvideo = 'name:"(.*?)",link:"(.*?)"'
                match = re.compile(regexvideo, re.DOTALL).findall(content2)
                for name, url in match:
                    # if 'adult' in name.lower():
                        # continue
                    pixmaps = piconlocal(name)
                    if os.path.exists(pixmaps):
                        # self.downloadPic(None, pixmaps)
                        pic = pixmaps
                    else:
                        pic = no_cover
                    self.names.append(name)
                    self.urls.append(url)
                    self.pics.append(pic)
                    self.infos.append(self.desc)
            elif 'countries' in self.desc.lower():
                content = Utils.ReadUrl2(Host, referer)
                n1 = content.find("var country=", 0)
                n2 = content.find("</script>", n1)
                content2 = content[n1:n2]
                regexvideo = 'name:"(.*?)",link:"(.*?)"'
                match = re.compile(regexvideo, re.DOTALL).findall(content2)
                for name, url in match:
                    pixmaps = piconlocal(name)
                    if os.path.exists(pixmaps):
                        # self.downloadPic(None, pixmaps)
                        pic = pixmaps
                    else:
                        pic = no_cover
                    self.names.append(name)
                    self.urls.append(url)
                    self.pics.append(pic)
                    self.infos.append(self.desc)
            elif 'years' in self.desc.lower():
                content = Utils.ReadUrl2(Host, referer)
                n1 = content.find("var years=", 0)
                n2 = content.find("var country", n1)
                content2 = content[n1:n2]
                regexvideo = 'name:"(.*?)",link:"(.*?)"'
                match = re.compile(regexvideo, re.DOTALL).findall(content2)
                for name, url in match:
                    pixmaps = piconlocal(name)
                    if os.path.exists(pixmaps):
                        # self.downloadPic(None, pixmaps)
                        pic = pixmaps
                    else:
                        pic = no_cover
                    self.names.append(name)
                    self.urls.append(url)
                    self.pics.append(pic)
                    self.infos.append(self.desc)
            elif 'a-z' in self.desc.lower():
                content = Utils.ReadUrl2(Host, referer)
                n1 = content.find('class="numeric-pagination post-list"><ul>', 0)
                n2 = content.find("/div><div", n1)
                content2 = content[n1:n2]
                # href=https://www.filmxy.online/movie-list/a/ >a</a></li><li><a
                regexvideo = 'https://www.filmxy.(.*?)/movie-list/(.*?)/.*?>(.*?)<'
                match = re.compile(regexvideo, re.DOTALL).findall(content2)
                for ext, url, name in match:
                    url1 = "https://www.filmxy." + ext + "/movie-list/" + url + "/"
                    pixmaps = piconlocal(name)
                    if os.path.exists(pixmaps):
                        # self.downloadPic(None, pixmaps)
                        pic = pixmaps
                    else:
                        pic = no_cover
                    self.names.append(name)
                    self.urls.append(url1)
                    self.pics.append(pic)
                    self.infos.append(self.desc)
            logdata("live_to_stream self.desc: ", self.desc)
            showlist(self.names, self['list'])
            # self['list'].moveToIndex(0)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in live_to_stream")

        return

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        try:
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            # pages
            if nextmodule == 'countries':
                self.session.open(pagesX, name, url, pic, nextmodule)
                return
            elif nextmodule == 'categories':
                self.session.open(pagesX, name, url, pic, nextmodule)
                return
            elif nextmodule == 'years':
                self.session.open(pagesX, name, url, pic, nextmodule)
                return
            # a-z
            elif nextmodule == 'a-z':
                self.session.open(azvideo, name, url, pic, nextmodule)
                return
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in live_to_stream")
        return

    def __layoutFinished(self):
        status = status_site()
        if status is True:
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.load_infos()
        self.load_poster()
        self.setTitle(self.setup_title)

    def load_infos(self):
        try:
            i = len(self.names)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                if info != '' or info != 'None':
                    self['desc'] = StaticText(info)
        except Exception as e:
            logdata('error info - v3', e)

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def cancel(self):
        self.close()

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            pixmaps = self.pics[idx]
            if str(res_plugin_path) in pixmaps:
                self.downloadPic(None, pixmaps)
                return
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
                    print("Error: can't find file or read data live_to_stream")
            else:
                self.poster_resize(no_cover)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in Playchoice")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as e:
                print("* error ** %s" % e)
                pass

    # def downloadPic(self, output, poster):
        # try:
            # if output is not None:
                # f = open(poster, 'wb')
                # f.write(output)
                # f.close()
            # # self.poster_resize(poster)
            # self["poster"].instance.setScale(1)
            # self["poster"].instance.setPixmapFromFile(poster)
            # self['poster'].show()
        # except Exception as e:
            # logdata('error ', e)
        # return

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as e:
            self.poster_resize(no_cover)
            print(e)
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        if not fileExists(png):
            png = no_cover
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class pagesX(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(skin_path, 'Filmxymain.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME FILMXY')
        self.setTitle(title_plug)
        self.list = []
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + cachefold)
        self['desc'] = StaticText()
        self['descadd'] = Label(_('Select your %s') % nextmodule)
        self["poster"] = Pixmap()
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('SERVER STATUS')
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.desc = nextmodule
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['DirectionActions',
                                     'OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'red': self.cancel,
                                                       'up': self.up,
                                                       'down': self.down,
                                                       'left': self.left,
                                                       'right': self.right,
                                                       'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(500, True)
        self.onLayoutFinish.append(self.__layoutFinished)

    def __layoutFinished(self):
        status = status_site()
        if status is True:
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(self.setup_title)
        self.poster_resize(self.pic)

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        # https://www.filmxy.pw/genre/action/page/2/
        pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        try:
            for page in pages:
                url1 = self.url + "page/" + str(page) + "/"
                name = "Page " + str(page)
                info = self.name
                self.names.append(name)
                self.urls.append(url1)
                pic = self.pic
                self.pics.append(pic)
                self.infos.append(info)
            logdata("pages nextmodule: ", self.desc)
            showlist(self.names, self['list'])
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in pagesX")
        return

    def okRun(self):
        i = len(self.pics)
        if i < 0:
            return
        try:
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            self.session.open(pagevideo3, name, url, pic, self.desc)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in pagesX")

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()

    def down(self):
        self[self.currentList].down()

    def left(self):
        self[self.currentList].pageUp()

    def right(self):
        self[self.currentList].pageDown()

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        else:
            self.poster_resize(no_cover)
            print('no cover.. error')
        return


class azvideo(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(skin_path, 'Filmxymain.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME FILMXY')
        self.setTitle(title_plug)
        self.list = []
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + cachefold)
        self['desc'] = StaticText()
        self['descadd'] = Label(_('Select you Stream'))
        self["poster"] = Pixmap()
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('SERVER STATUS')
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.desc = nextmodule
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['EPGSelectActions',
                                     'DirectionActions',
                                     'OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'red': self.cancel,
                                                       'up': self.up,
                                                       'down': self.down,
                                                       'left': self.left,
                                                       'right': self.right,
                                                       'epg': self.showIMDB,
                                                       'info': self.showIMDB,
                                                       'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(500, True)
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.left)
        except:
            self.leftt.callback.append(self.left)
        self.leftt.start(1000, True)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        try:
            i = len(self.names)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                print('show imdb/tmdb')
        except Exception as e:
            print(e)
            print("Error: can't find azvideo in live_to_stream")

    def __layoutFinished(self):
        status = status_site()
        if status is True:
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(self.setup_title)
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                if info != '' or info != 'None':
                    self['desc'] = StaticText(info)
        except Exception as e:
            logdata('error info - v3', e)

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl2(self.url, referer)
        if PY3:
            content = six.ensure_str(content)
        try:
            n1 = content.find("class=loaded-data><p", 0)
            n2 = content.find('"><div', n1)
            content2 = content[n1:n2]
            regexvideo = 'href=(.*?)/ rel.*?target=_blank>(.*?)<'
            match = re.compile(regexvideo, re.DOTALL).findall(content2)
            for url, name in match:
                url = url.strip()
                name = name.strip()
                name = html_conv.html_unescape(name)
                url1 = url + "/"
                pixmaps = piconlocal(name)
                if os.path.exists(pixmaps):
                    # self.downloadPic(None, pixmaps)
                    pic = pixmaps
                else:
                    pic = no_cover
                self.names.append(name)
                self.urls.append(url1)
                self.pics.append(pic)
                self.infos.append(self.desc)
            # logdata("azvideo nextmodule: ", self.desc)
            showlist(self.names, self['list'])
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in azvideo")

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        try:
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            desc = self.infos[idx]
            logdata("azvideo name: ", name)
            self.session.open(Video5list, name, url, pic, desc)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in azvideo okRun")

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            pixmaps = self.pics[idx]
            if str(res_plugin_path) in pixmaps:
                self.downloadPic(None, pixmaps)
                return
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    print("debug pixmaps p:", pixmaps)
                    print("debug pixmaps p:", type(pixmaps))
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
                    print("Error: can't find file in azvideo")
            else:
                self.poster_resize(no_cover)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in Playchoice")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as e:
                print("* error ** %s" % e)
                pass

    # def downloadPic(self, output, poster):
        # try:
            # if output is not None:
                # f = open(poster, 'wb')
                # f.write(output)
                # f.close()
            # # self.poster_resize(poster)
            # self["poster"].instance.setScale(1)
            # self["poster"].instance.setPixmapFromFile(poster)
            # self['poster'].show()
        # except Exception as e:
            # logdata('error ', e)
        # return

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as e:
            self.poster_resize(no_cover)
            print(e)
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        else:
            print('no cover.. error')
        return


class pagevideo3(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(skin_path, 'Filmxymain.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME FILMXY')
        self.setTitle(title_plug)
        self.list = []
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + cachefold)
        self['desc'] = StaticText()
        self['descadd'] = Label('')
        self["poster"] = Pixmap()
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('SERVER STATUS')
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infosadd = []
        self.sizes = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.desc = nextmodule
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['EPGSelectActions',
                                     'DirectionActions',
                                     'OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'red': self.cancel,
                                                       'up': self.up,
                                                       'down': self.down,
                                                       'left': self.left,
                                                       'right': self.right,
                                                       'epg': self.showIMDB,
                                                       'info': self.showIMDB,
                                                       'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(500, True)
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.left)
        except:
            self.leftt.callback.append(self.left)
        self.leftt.start(500, True)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        try:
            i = len(self.names)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                logdata("show imdb/tmdb ", text_clear)
        except Exception as e:
            print(e)
            print("Error: can't find pagevideo3 in live_to_stream")

    def __layoutFinished(self):
        status = status_site()
        if status is True:
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(self.setup_title)

    def load_infos(self):
        try:
            i = len(self.names)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                info = self.infos[idx]
                infoadd = self.infosadd[idx]
                size2 = self.sizes[idx]
                intot = ''
                if info != '' or info != 'None':
                    info = html_conv.html_unescape(info)
                    self['desc'].setText(info)
                if infoadd != '':
                    intot = str(infoadd)  # + '\n' + str(size2)
                    # if size2:
                    intot = str(infoadd) + '\n' + str(size2)
                    self['descadd'].setText(intot)
            # logdata('info = ', info)
            # logdata('intot2 = ', intot)
            return
        except Exception as e:
            self['desc'].setText(' ')
            self['descadd'].setText(' ')
            logdata(e)
            logdata("Error: can't find pagevideo3 in load_infos")

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infosadd = []
        self.sizes = []
        self.infos = []
        content = Utils.ReadUrl2(self.url, referer)
        if PY3:
            content = six.ensure_str(content)
        try:
            '''
            <div
            class="col-md-2 col-sm-3 col-xs-6 custom-col"><div
            class=single-post><div
            class=post-thumbnail>
            <a
            href=https://www.filmxy.pw/the-quiet-2005/ >
            <img
            width=250 height=350 data-src=https://www.cdnzone.org/uploads/2022/11/04/The-Quiet-2005-Cover.jpg src=https://www.cdnzone.org/asset/images/1px.png alt="The Quiet Cover">
            </a><div
            class="m-type post">Movie</div><div
            class="m-quality green">HD/Web-DL</div></div><div
            class=post-description><div
            class=post-title><h2>The Quiet (2005)</h2></div><div
            class=imdb-details><p><b>IMDb: </b>6.2/10</p></div><div
            class=available-quality><p>720p | 1080p</p></div><div
            class=genre><p><b>Ganre: </b>Crime, Drama, Thriller</p></div><div
            class=mpa><p><b>MPA: </b>R</p></div><div
            class=size><p><b>Size: </b>883.62 MB | 1.6 GB</p></div><div
            class=story><p>This film receives a 10 for disturbing subject matter. It is at times very difficult to watch. The characters are troubled, each in his/her own way. It feels edgy and often very foreign. With that warning, I must say that on some level I enjoyed the film. Technically it is superb. The character development is [&hellip;]</p></div><div

            class=story></div><div

            class=categories><p><b>Category: </b> <a
            href=https://www.filmxy.pw/genre/adult/ rel="category tag">Adult</a>, <a
            href=https://www.filmxy.pw/genre/crime/ rel="category tag">Crime</a>, <a
            href=https://www.filmxy.pw/genre/drama/ rel="category tag">Drama</a>, <a
            href=https://www.filmxy.pw/genre/thriller/ rel="category tag">Thriller</a></p></div></div></div></div><div

            regexvideo = 'class=post-thumbnail>.*?href=(.*?)/ >.*?data-src=(.*?) src.*?title><h2>(.*?)<'

            class=single-post><div
            class=post-thumbnail>
            <a
            href=https://www.filmxy.pw/route-10-2022/ >
            <img
            width=250 height=350 data-src=https://www.cdnzone.org/uploads/2022/10/30/Route-10-2022-Cover.jpg src=https://www.cdnzone.org/asset/images/1px.png alt="Route 10 Cover">
            </a><div
            class="m-type post">Movie</div><div
            class="m-quality green">HD/Web-DL</div></div><div
            class=post-description><div
            class=post-title><h2>Route 10 (2022)</h2></div><div
            class=imdb-details><p><b>IMDb: </b>6.1/10</p></div><div
            class=available-quality><p>720p | 1080p</p></div><div
            class=genre><p><b>Ganre: </b>Action, Drama, Thriller</p></div><div
            class=mpa><p><b>MPA: </b>N/A</p></div><div
            class=size><p><b>Size: </b>749.68 MB | 1.5 GB</p></div><div
            class=story></div><div
            class=categories><p><b>Category: </b> <a
            href=https://www.filmxy.pw/genre/action/ rel="category tag">Action</a>, <a
            href=https://www.filmxy.pw/genre/drama/ rel="category tag">Drama</a>, <a
            href=https://www.filmxy.pw/genre/thriller/ rel="category tag">Thriller</a></p></div></div></div></div><div

            n1 = content.find("cat-description", 0)
            n2 = content.find("numeric-pagination>", n1)
            content2 = content[n1:n2]
            regexvideo = 'post-thumbnail>.*?href=(.*?)>.*?data-src=(.*?)src.*?title><h2>(.*?)<.*?Ganre:.*?</b>(.*?)</p>.*?Size:.*?</b>(.*?)</p>.*?story><p>(.*?)</p>'
            '''
            regexvideo = 'post-thumbnail>.*?href=(.*?)>.*?data-src=(.*?)src.*?title><h2>(.*?)<.*?Ganre:.*?</b>(.*?)</p>.*?Size:.*?(.*?)</p>.*?story>(.*?)</div>'
            match = re.compile(regexvideo, re.DOTALL).findall(content)
            for url, pic, name, infoadd, size, info in match:
                url1 = url.replace(' ', '')
                url1 = url1.strip()  # + "/"
                pic = pic.strip()  # .replace('https', 'http')
                name = name.strip()
                name = html_conv.html_unescape(name)
                size = size.replace('</b>', '').replace(' ', '')
                size2 = 'Size ' + str(size)
                info = info.replace('<p>', '').replace('</p>', '').replace('&hellip;', '...')
                self.urls.append(url1)
                self.pics.append(pic)
                self.names.append(name)
                self.infosadd.append(infoadd)
                self.sizes.append(size2)
                self.infos.append(info)
            logdata("pagevideo3 nextmodule: ", self.desc)
            showlist(self.names, self['list'])
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in pagevideo3")
        return

    def okRun(self):
        try:
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            info = self.infos[idx]
            logdata("pagevideo3 name: ", name)
            self.session.open(Video5list, name, url, pic, info)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in pagevideo3")

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            pixmaps = self.pics[idx]

            # if str(res_plugin_path) in pixmaps:
                # self.downloadPic(None, pixmaps)
                # return
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
                    print("Error: can't find file in pagevideo3")
            else:
                self.poster_resize(no_cover)
        except Exception as e:
            print(e)
            print("Error: pagevideo3")
        return

    # def downloadPic(self, output, poster):
        # try:
            # if output is not None:
                # f = open(poster, 'wb')
                # f.write(output)
                # f.close()
            # # self.poster_resize(poster)
            # self["poster"].instance.setScale(1)
            # self["poster"].instance.setPixmapFromFile(poster)
            # self['poster'].show()
        # except Exception as e:
            # logdata('error ', e)
        # return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as e:
                print("* error ** %s" % e)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as e:
            self.poster_resize(no_cover)
            print(e)
            print('exe downloadError')

    def poster_resize(self, png):
        if not fileExists(png):
            png = no_cover
        self.picload = ePicLoad()
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.scale = eAVSwitch().getFramebufferScale()
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class Video5list(Screen):
    def __init__(self, session, name, url, pic, info):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = os.path.join(skin_path, 'Filmxymain.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('HOME FILMXY')
        self.setTitle(title_plug)
        self.list = []
        self['list'] = self.list
        self['list'] = rvList([])
        self['info'] = Label(name)
        self['pth'] = Label('')
        self['pth'].setText(_('Cache folder ') + cachefold)
        self['desc'] = StaticText()
        self['descadd'] = Label('')
        self["poster"] = Pixmap()
        self['statusgreen'] = Pixmap()
        self['statusgreen'].hide()
        self['statusred'] = Pixmap()
        self['statusred'].hide()
        self['status'] = Label('SERVER STATUS')
        # self["poster"].hide()
        self.picload = ePicLoad()
        self.scale = eAVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.desc = html_conv.html_unescape(info)
        self.downloading = False
        self.currentList = 'list'
        self['title'] = Label(title_plug)
        self['actions'] = ActionMap(['EPGSelectActions',
                                     'DirectionActions',
                                     'OkCancelActions',
                                     'ColorActions'], {'ok': self.okRun,
                                                       'red': self.cancel,
                                                       'up': self.up,
                                                       'down': self.down,
                                                       'left': self.left,
                                                       'right': self.right,
                                                       'epg': self.showIMDB,
                                                       'info': self.showIMDB,
                                                       'cancel': self.cancel}, -2)
        self.readJsonTimer = eTimer()
        try:
            self.readJsonTimer_conn = self.readJsonTimer.timeout.connect(self.readJsonFile)
        except:
            self.readJsonTimer.callback.append(self.readJsonFile)
        self.readJsonTimer.start(500, True)
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.left)
        except:
            self.leftt.callback.append(self.left)
        self.leftt.start(1000, True)
        self.onLayoutFinish.append(self.__layoutFinished)

    def showIMDB(self):
        try:
            i = len(self.names)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                logdata('show imdb/tmdb')
        except Exception as e:
            print(e)
            print("Error: can't find Video5list in Video5list")

    def __layoutFinished(self):
        status = status_site()
        if status is True:
            self['statusgreen'].show()
            self['statusred'].hide()
            self['status'].setText('SERVER ON')
        else:
            self['statusgreen'].hide()
            self['statusred'].show()
            self['status'].setText('SERVER OFF')
        self.setTitle(self.setup_title)
        self.load_infos()
        self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            if i > 0:
                info = self.desc
                if info != '' or info != 'None':
                    self['desc'].setText(info)
                    self['descadd'].setText('Stream Link n°' + str(i))
                else:
                    self['desc'].setText(' ')
                    self['descadd'].setText('No Stream Link available')
            else:
                self['desc'].setText(' ')
                self['descadd'].setText('No Stream Link available')
        except Exception as e:
            logdata('error info - v5', e)

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl2(self.url, referer)
        # if PY3:
            # content = six.ensure_str(content)
        try:
            # regexvideo = 'id=tab-download.*?href=(.*?)target'
            # regexvideo = 'id=tab-download.*?href=(.*?)target.*?class=movie-poster.*?data-src=(.*?)src'
            # class=movie-poster>
            # <img
            # width=250 height=350 data-src=https://www.cdnzone.org/uploads/2017/09/A-2nd-Hand-Lover-2015-cover.jpg src
            regexvideo = 'class=movie-poster.*?data-src=(.*?) src.*?id=main-down.*?href=(.*?) target'
            match = re.compile(regexvideo, re.DOTALL).findall(content)
            for pic, url in match:
                picx = pic.strip  # .replace('https', 'http').replace(' ', '').strip()
                url = url.replace(" ", "").strip()
                content2 = Utils.ReadUrl2(url, referer)
                regexvideo2 = '<li class="signle-link"><a href="(.*?)".*?<span>(.*?)</span>.*?<strong>(.*?)</strong>'
                match2 = re.compile(regexvideo2, re.DOTALL).findall(content2)
                for url, name1, name2 in match2:
                    name1 = name1.replace("-", "").replace(" ", "")
                    name = unquote(self.name) + "-" + name1 + "-" + name2
                    name = html_conv.html_unescape(name)
                    pic = str(picx)
                    info = self.desc
                    if "racaty" not in name.lower():
                        continue
                    self.names.append(name)
                    self.urls.append(url)
                    self.pics.append(pic)
                    self.infos.append(info)
            # logdata("Video5list nextmodule: ", self.desc)
            showlist(self.names, self['list'])
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in Video5list")
        return

    def okRun(self):
        i = len(self.names)
        if i < 0:
            return
        try:
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            url = self.urls[idx]
            info = self.infos[idx]
            pic = self.pics[idx]
            logdata("Video5list name: ", name)
            logdata("Video5list url: ", url)
            self.session.open(Playchoice, name, url, pic, info)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in Video5list 2 ")

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()
        self.load_infos()
        self.load_poster()

    def down(self):
        self[self.currentList].down()
        self.load_infos()
        self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()
        self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()
        self.load_poster()

    def load_poster(self):
        try:
            i = len(self.pics)
            if i < 0:
                return
            idx = self['list'].getSelectionIndex()
            pixmaps = self.pics[idx]
            if str(res_plugin_path) in pixmaps:
                self.poster_resize(pixmaps)
                # self.downloadPic(None, pixmaps)
                return
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as e:
                    print(e)
                    print("Error: can't find file in Video5list")
            else:
                self.poster_resize(no_cover)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in Playchoice")
        return

    # def downloadPic(self, output, poster):
        # try:
            # if output is not None:
                # f = open(poster, 'wb')
                # f.write(output)
                # f.close()
            # # self.poster_resize(poster)
            # self["poster"].instance.setScale(1)
            # self["poster"].instance.setPixmapFromFile(poster)
            # self['poster'].show()
        # except Exception as e:
            # logdata('error ', e)
        # return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as e:
                print("* error ** %s" % e)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as e:
            self.poster_resize(no_cover)
            print(e)
            print('exe downloadError')

    def poster_resize(self, png):
        if not fileExists(png):
            png = no_cover
        self.picload = ePicLoad()
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.scale = eAVSwitch().getFramebufferScale()
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class Playchoice(Screen):
    def __init__(self, session, name, url, pic, desc):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'Playchoice.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        f.close()
        self.setup_title = ('Select Player Stream')
        self.list = []
        self.names = []
        self.urls = []
        self.name1 = cleantitle(name)
        self.url = url
        self.desc = desc
        self.pic = pic
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['list'] = rvList([])
        self['info'] = Label()
        self['info'].setText(name)
        self['desc'] = StaticText()
        self['title'] = Label(title_plug)
        self['poster'] = Pixmap()
        self['key_red'] = Button(_('Back'))
        self['key_green'] = Button(_('Select'))
        self['key_yellow'] = Button(_('Movie'))
        self['progress'] = ProgressBar()
        self['progresstext'] = StaticText()
        self["progress"].hide()
        self.downloading = False
        self['actions'] = ActionMap(['ColorActions',
                                     'CancelActions',
                                     'TimerEditActions',
                                     'OkCancelActions',
                                     'ButtonSetupActions',
                                     'InfobarInstantRecord'], {'red': self.cancel,
                                                               'green': self.okClicked,
                                                               'back': self.cancel,
                                                               'cancel': self.cancel,
                                                               # 'rec': self.runRec,
                                                               'yellow': self.taskManager,
                                                               # 'instantRecord': self.runRec,
                                                               # 'ShortRecord': self.runRec,
                                                               'ok': self.okClicked}, -2)
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.load_poster)
        except:
            self.leftt.callback.append(self.load_poster)
        self.leftt.start(500, True)
        self.onLayoutFinish.append(self.load_infos)
        self.onLayoutFinish.append(self.openTest)
        # return

    def load_infos(self):
        try:
            if self.desc != '' or self.desc != 'None':
                self['desc'].setText(self.desc)
            else:
                self['desc'].setText('No Epg')
        except Exception as e:
            logdata('error info - v4', e)

    def taskManager(self):
        self.session.open(StreamTasks)

    def runRec(self, url):
        # if 'None' not in str(url):
            # self.namem3u = self.name1
        self.urlx = url
        if self.downloading is True:
            self.session.open(MessageBox, _('You are already downloading!!!'), MessageBox.TYPE_INFO, timeout=5)
            return
        else:
            self.session.openWithCallback(self.download_m3u, MessageBox, _("DOWNLOAD VIDEO?\n%s" % self.name1), type=MessageBox.TYPE_YESNO, timeout=5, default=True)
        # else:
            # self.session.open(MessageBox, _('No link available'), MessageBox.TYPE_INFO, timeout=5)

    def download_m3u(self, result):
        if result:
            logdata('--------------not m3u8-----------------')
            print('-------------- download init -----------------')
            self.urlx = self.urlx.replace(' ', '%20')
            self.urlx = self.urlx[:self.urlx.rfind("|")]
            # print('new url: ', self.urlx)
            path = urlparse(self.urlx).path
            ext = splitext(path)[1]
            filename = self.name1
            if ext not in EXTDOWN:
                ext = '.mp4'
            fileTitle = filename.lower() + ext
            self.in_tmp = Path_Movies + fileTitle
            logdata('path download = ', self.in_tmp)
            try:
                # useragent = "--header='User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'"

                # import subprocess
                # # cmd = "wget %s -c '%s' -O '%s'" % (useragent, self.urlx, self.in_tmp)
                # # if "https" in str(self.urlx):
                    # # cmd = "wget --no-check-certificate -U %s -c '%s' -O '%s'" % (useragent, self.urlx, self.in_tmp)

                # cmd = "wget -U '%s' -c '%s' -O '%s'" % ('Enigma2 - Filmxy Plugin', str(self.urlx), self.in_tmp)
                # if "https" in str(self.urlx):
                    # cmd = "wget --no-check-certificate -U '%s' -c '%s' -O '%s'" % ('Enigma2 - tvAddon Plugin', str(self.urlx), self.in_tmp)

                # myCmd = "%s" % str(cmd)
                # subprocess.Popen(myCmd, shell=True, executable='/bin/bash')
                # self['info'].setText(_('Download in progress... %s' % fileTitle))
                # self.downloading = True
                # pmovies = True

                cmd = "wget -U '%s' -c '%s' -O '%s'" % ('Enigma2 - Filxy Plugin', self.urlx, self.in_tmp)
                if "https" in str(self.urlx):
                    cmd = "wget --no-check-certificate -U '%s' -c '%s' -O '%s'" % ('Enigma2 - Filxy Plugin', self.urlx, self.in_tmp)
                print('cmd comand wget: ', cmd)
                try:
                    ui = True
                    job_manager.AddJob(downloadJob(self, cmd, self.in_tmp, fileTitle))
                    self.downloading = True
                    pmovies = True
                except Exception as e:
                    print(e)
                    pass
            except URLError as e:
                logdata("Download failed !!\n%s" % e)
                self.session.openWithCallback(self.ImageDownloadCB, MessageBox, _("Download Failed !!") + "\n%s" % e, type=MessageBox.TYPE_ERROR)
                self.downloading = False
                pmovies = False
        else:
            self.downloading = False

    def ImageDownloadCB(self, ret):
        if ret:
            return
        if job_manager.active_job:
            job_manager.active_job = None
            self.close()
            return
        if len(job_manager.failed_jobs) == 0:
            self.LastJobView()
        else:
            self.downloading = False
            self.session.open(MessageBox, _("Download Failed !!"), type=MessageBox.TYPE_ERROR)

    def showError(self, error):
        self.downloading = False
        self.session.open(MessageBox, _('Download Failed!!!'), MessageBox.TYPE_INFO, timeout=5)

    def LastJobView(self):
        currentjob = None
        for job in job_manager.getPendingJobs():
            currentjob = job
        if currentjob is not None:
            self.session.open(JobView, currentjob)
        else:
            self.downloading = False

    def openTest(self):
        url = self.url
        self.names = []
        self.urls = []
        self.names.append('Play Now')
        self.urls.append(url)
        self.names.append('Download Now- Test')
        self.urls.append(url)
        self.names.append('Play HLS')
        self.urls.append(url)
        self.names.append('Play TS')
        self.urls.append(url)
        self.names.append('Streamlink')
        self.urls.append(url)
        showlist(self.names, self['list'])

    def racatyx(self, name, url):
        urlx = url
        name = name
        if ("vidcloud" in name.lower()) or ("googlelink" in name.lower()) or ("dl" in name.lower()) or ("cdn" in name.lower()) or ("gvideo" in name.lower()):
            return urlx
        else:
            if "mediashore" in name.lower():
                from .resolver.fembed import FEmbedResolver
                res = FEmbedResolver()
                return res.get_media_url(urlx)
            elif "racaty" in name.lower():
                from .resolver.racaty import RacatyResolver
                res = RacatyResolver()
                return res.get_media_url(urlx)
            elif "sbfast" in name.lower():
                from .resolver.streamsb import StreamSBResolver
                res = StreamSBResolver()
                return res.get_media_url(urlx)

    def okClicked(self):
        i = len(self.names)
        if i < 0:
            return
        try:
            idx = self['list'].getSelectionIndex()
            name = self.name1.replace("%28%", "(").replace("%29%", ")")
            url = self.url
            cmd = ''
            if idx == 0:
                url = self.racatyx(name, url)
                url = url[:url.rfind("|")]
                url = url.replace(' ', '%20')
                print('okClicked new url: ', url)
                self.play(name, url)
            elif idx == 1:
                url = self.url
                self.urlx = self.racatyx(name, url)
                self.runRec(self.urlx)
            elif idx == 2:
                self.name = self.name1
                url = self.url.replace(':', '%3a')
                try:
                    os.remove('/tmp/hls.avi')
                except:
                    pass
                header = ''
                cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/filmxy/resolver/hlsclient.py" "' + url + '" "1" "' + header + '" + &'
                os.system(cmd)
                os.system('sleep 3')
                url = '/tmp/hls.avi'
                self.play(self.name, url)
            elif idx == 3:
                url = self.url.replace(':', '%3a')
                try:
                    os.remove('/tmp/hls.avi')
                except:
                    pass
                cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/filmxy/resolver/tsclient.py" "' + url + '" "1" + &'
                os.system(cmd)
                os.system('sleep 3')
                url = '/tmp/hls.avi'
                self.name = self.name1
                self.play(self.name, url)
            else:
                if idx == 4:
                    self.name = self.name1
                    url = self.url.replace(':', '%3a')
                    self.play2(self.name, url)
            return
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in Playchoice")

    def playfile(self, serverint):
        if 'None' not in str(self.url):
            self.serverList[serverint].play(self.session, self.url, self.name)
        else:
            self.session.open(MessageBox, _('No link available'), MessageBox.TYPE_INFO, timeout=5)
        self.close()

    def play(self, name, url):
        try:
            # print("Playstream2 name: ", name)
            # print("Playstream2 url: ", url)
            if 'None' not in str(url) or url != '':
                self.session.open(Playstream2, name, url)
            else:
                self.session.open(MessageBox, _('No link available'), MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            logdata('error play ', e)

    def play2(self, name, url):
        if Utils.isStreamlinkAvailable():
            name = self.name
            url = url
            logdata('In filmxy url =', url)
            ref = '5002:0:1:0:0:0:0:0:0:0:' + 'http%3a//127.0.0.1%3a8088/' + str(url)
            sref = eServiceReference(ref)
            logdata('SREF: ', sref)
            sref.setName(name)
            self.session.open(Playstream2, name, sref)
        else:
            self.session.open(MessageBox, _('Install Streamlink first'), MessageBox.TYPE_INFO, timeout=5)

    def cancel(self):
        try:
            self.session.nav.stopService()
            self.session.nav.playService(self.srefInit)
            self.close()
        except:
            pass

    def load_poster(self):
        try:
            i = len(self.names)
            if i < 0:
                return
            pixmaps = self.pic
            # if str(res_plugin_path) in pixmaps:
            self.downloadPic(None, pixmaps)
                # return
            # pixmaps = six.ensure_binary(self.pics[idx])
            # if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                # try:
                    # if PY3:
                        # pixmaps = six.ensure_binary(self.pic)
                    # if pixmaps.startswith(b"https") and sslverify:
                        # parsed_uri = urlparse(pixmaps)
                        # domain = parsed_uri.hostname
                        # sniFactory = SNIFactory(domain)
                        # # if six.PY3:
                            # # pixmaps = pixmaps.encode()
                        # downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    # else:
                        # downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                # except Exception as e:
                    # print(e)
                    # print("Error: can't find file or read data live_to_stream")
            # else:
                # self.poster_resize(no_cover)
        except Exception as e:
            print(e)
            print("Error: can't find file or read data in Playchoice")
        return

    def downloadPic(self, output, poster):
        try:
            if output is not None:
                f = open(poster, 'wb')
                f.write(output)
                f.close()
            # self.poster_resize(poster)
            self["poster"].instance.setScale(1)
            self["poster"].instance.setPixmapFromFile(poster)
            self['poster'].show()
        except Exception as e:
            logdata('error ', e)
        return

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as e:
            self.poster_resize(no_cover)
            print('exe downloadError', e)

    def poster_resize(self, png):
        if not fileExists(png):
            png = no_cover
        self.picload = ePicLoad()
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.scale = eAVSwitch().getFramebufferScale()
        self.picload.setPara((size.width(),
                              size.height(),
                              self.scale[0],
                              self.scale[1],
                              False,
                              1,
                              '#FF000000'))
        if Utils.DreamOS():
            self.picload.startDecode(png, False)
        else:
            self.picload.startDecode(png, 0, 0, False)
        ptr = self.picload.getData()
        if ptr is not None:
            self['poster'].instance.setPixmap(ptr)
            self['poster'].show()
        return


class TvInfoBarShowHide():
    """ InfoBar show/hide control, accepts toggleShow and hide actions, might start
    fancy animations. """
    STATE_HIDDEN = 0
    STATE_HIDING = 1
    STATE_SHOWING = 2
    STATE_SHOWN = 3
    skipToggleShow = False

    def __init__(self):
        self["ShowHideActions"] = ActionMap(["InfobarShowHideActions"], {"toggleShow": self.OkPressed, "hide": self.hide}, 1)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
            iPlayableService.evStart: self.serviceStarted,
        })
        self.__state = self.STATE_SHOWN
        self.__locked = 0
        self.hideTimer = eTimer()
        try:
            self.hideTimer_conn = self.hideTimer.timeout.connect(self.doTimerHide)
        except:
            self.hideTimer.callback.append(self.doTimerHide)
        self.hideTimer.start(5000, True)
        self.onShow.append(self.__onShow)
        self.onHide.append(self.__onHide)

    def OkPressed(self):
        self.toggleShow()

    def __onShow(self):
        self.__state = self.STATE_SHOWN
        self.startHideTimer()

    def __onHide(self):
        self.__state = self.STATE_HIDDEN

    def serviceStarted(self):
        if self.execing:
            if config.usage.show_infobar_on_zap.value:
                self.doShow()

    def startHideTimer(self):
        if self.__state == self.STATE_SHOWN and not self.__locked:
            self.hideTimer.stop()
            idx = config.usage.infobar_timeout.index
            if idx:
                self.hideTimer.start(idx * 1500, True)

    def doShow(self):
        self.hideTimer.stop()
        self.show()
        self.startHideTimer()

    def doTimerHide(self):
        self.hideTimer.stop()
        if self.__state == self.STATE_SHOWN:
            self.hide()

    def toggleShow(self):
        if self.skipToggleShow:
            self.skipToggleShow = False
            return
        if self.__state == self.STATE_HIDDEN:
            self.show()
            self.hideTimer.stop()
        else:
            self.hide()
            self.startHideTimer()

    def lockShow(self):
        try:
            self.__locked += 1
        except:
            self.__locked = 0
        if self.execing:
            self.show()
            self.hideTimer.stop()
            self.skipToggleShow = False

    def unlockShow(self):
        try:
            self.__locked -= 1
        except:
            self.__locked = 0
        if self.__locked < 0:
            self.__locked = 0
        if self.execing:
            self.startHideTimer()

    def debug(obj, text=""):
        print(text + " %s\n" % obj)


class Playstream2(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarAudioSelection, TvInfoBarShowHide, InfoBarSubtitleSupport, SubsSupportStatus, SubsSupport):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    # screen_timeout = 4000

    def __init__(self, session, name, url):
        global streaml, _session
        _session = session
        streaml = False
        Screen.__init__(self, session)
        self.session = session
        self.skinName = 'MoviePlayer'
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarBase.__init__(self, steal_current_service=True)
        TvInfoBarShowHide.__init__(self)
        InfoBarSubtitleSupport.__init__(self)
        InfoBarAudioSelection.__init__(self)
        try:
            self.init_aspect = int(self.getAspect())
        except:
            self.init_aspect = 0
        try:
            SubsSupport.__init__(self, searchSupport=True, embeddedSupport=True)
            SubsSupportStatus.__init__(self)
        except:
            pass
        self.new_aspect = self.init_aspect
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self.service = None
        self.name = html_conv.html_unescape(name)
        self.icount = 0
        self.url = url
        self.state = self.STATE_PLAYING
        self['actions'] = ActionMap(['MoviePlayerActions',
                                     'MovieSelectionActions',
                                     'MediaPlayerActions',
                                     'EPGSelectActions',
                                     'MediaPlayerSeekActions',
                                     'ButtonSetupActions',
                                     'OkCancelActions',
                                     'InfobarShowHideActions',
                                     'InfobarActions',
                                     'ColorActions',
                                     'InfobarSeekActions'], {'leavePlayer': self.cancel,
                                                             'epg': self.showIMDB,
                                                             'info': self.showIMDB,
                                                             'tv': self.cicleStreamType,
                                                             'stop': self.leavePlayer,
                                                             'red': self.cicleStreamType,
                                                             'cancel': self.cancel,
                                                             'back': self.cancel}, -1)
        InfoBarSeek.__init__(self, actionmap='InfobarSeekActions')
        if '8088' in str(self.url):
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            self.onFirstExecBegin.append(self.cicleStreamType)
        # self.onFirstExecBegin.append(self.openPlay(url))
        # self.onClose.append(self.cancel)
        return

    def getAspect(self):
        return eAVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {
            0: '4:3 Letterbox',
            1: '4:3 PanScan',
            2: '16:9',
            3: '16:9 always',
            4: '16:10 Letterbox',
            5: '16:10 PanScan',
            6: '16:9 Letterbox'
        }[aspectnum]

    def setAspect(self, aspect):
        map = {
            0: '4_3_letterbox',
            1: '4_3_panscan',
            2: '16_9',
            3: '16_9_always',
            4: '16_10_letterbox',
            5: '16_10_panscan',
            6: '16_9_letterbox'
        }
        config.av.aspectratio.setValue(map[aspect])
        try:
            eAVSwitch().setAspectRatio(aspect)
        except:
            pass

    def av(self):
        temp = int(self.getAspect())
        temp += 1
        if temp > 6:
            temp = 0
        self.new_aspect = temp
        self.setAspect(temp)

    def showIMDB(self):
        try:
            text_clear = self.name
            if returnIMDB(text_clear):
                logdata("show imdb/tmdb ", text_clear)
        except Exception as e:
            print(e)
            print("Error: can't find Playstream2 in live_to_stream")

    def slinkPlay(self, url):
        name = self.name
        ref = "{0}:{1}".format(url, name)
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openPlay(self, servicetype, url):
        name = self.name
        url = url.replace(' ', '%20')
        url = url.replace(':', '%3a')

        # servicetype = config.plugins.filmxy.services.getValue()
        logdata("xmbc url 2=", url)
        url = url.replace("&", "AxNxD").replace("=", "ExQ")
        logdata("xmbc url 4=", url)
        data = "&url=" + url + "&name=" + name + "\n"
        logdata("xmbc data B=", data)
        logdata("xmbc url 6=", url)
        self.timerCache = eTimer()
        try:
            self.timerCache.stop()
        except:
            pass

        try:
            self.timerCache.callback.append(clear_caches)
        except:
            self.timerCache_conn = self.timerCache.timeout.connect(clear_caches)
        self.timerCache.start(600000, False)
        # url = url[:url.rfind("|")]
        print('new url: ', url)
        ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url, name)
        if streaml is True:
            url = 'http://127.0.0.1:8088/' + str(url)
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url, name)
        logdata('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cicleStreamType(self):
        global streml
        streaml = False
        from itertools import cycle, islice
        self.servicetype = str(config.plugins.filmxy.services.value)
        url = str(self.url)
        if str(os.path.splitext(url)[-1]) == ".m3u8":
            if self.servicetype == "1":
                self.servicetype = "4097"
        currentindex = 0
        streamtypelist = ["4097"]

        if streamlink:
            streamtypelist.append("5002")  # ref = '5002:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/' + url
            streaml = True
        if os.path.exists("/usr/bin/gstplayer"):
            streamtypelist.append("5001")
        if os.path.exists("/usr/bin/exteplayer3"):
            streamtypelist.append("5002")
        if os.path.exists("/usr/bin/apt-get"):
            streamtypelist.append("8193")
        for index, item in enumerate(streamtypelist, start=0):
            if str(item) == str(self.servicetype):
                currentindex = index
                break
        nextStreamType = islice(cycle(streamtypelist), currentindex + 1, None)
        self.servicetype = str(next(nextStreamType))
        if config.plugins.filmxy.servicesforce.getValue() is True:
            self.servicetype = str(config.plugins.filmxy.services.getValue())
            print('servicetype force: ', self.servicetype)
        logdata('servicetype1: ', self.servicetype)
        self.openPlay(self.servicetype, url)

    def up(self):
        pass

    def down(self):
        self.up()

    def doEofInternal(self, playing):
        self.close()

    def __evEOF(self):
        self.end = True

    def showVideoInfo(self):
        if self.shown:
            self.hideInfobar()
        if self.infoCallback is not None:
            self.infoCallback()
        return

    def showAfterSeek(self):
        if isinstance(self, TvInfoBarShowHide):
            self.doShow()

    def cancel(self):
        if os.path.exists('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)
        try:
            self.timerCache.stop()
        except:
            pass
        if not self.new_aspect == self.init_aspect:
            try:
                self.setAspect(self.init_aspect)
            except:
                pass
        streaml = False
        self.close()

    def leavePlayer(self):
        self.close()


class myconfig(Screen, ConfigListScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        skin = os.path.join(skin_path, 'myconfig.xml')
        f = open(skin, 'r')
        self.skin = f.read()
        f.close()
        self.setTitle(title_plug)
        self.setup_title = title_plug
        self.onChangedEntry = []
        self.session = session
        self['description'] = Label('')
        self["paypal"] = Label()
        self['info'] = Label('')
        self['key_yellow'] = Button(_('Choice'))
        self['key_green'] = Button(_('Save'))
        self['key_red'] = Button(_('Back'))
        self["key_blue"] = Button(_('Empty Cache'))
        self['title'] = Label(title_plug)
        self["setupActions"] = ActionMap(['OkCancelActions',
                                          'DirectionActions',
                                          'ColorActions',
                                          'ButtonSetupActions',
                                          'VirtualKeyboardActions'], {'cancel': self.extnok,
                                                                      'red': self.extnok,
                                                                      'back': self.close,
                                                                      'left': self.keyLeft,
                                                                      'right': self.keyRight,
                                                                      'showVirtualKeyboard': self.KeyText,
                                                                      'yellow': self.Ok_edit,
                                                                      'ok': self.Ok_edit,
                                                                      'blue': self.cachedel,
                                                                      'green': self.msgok}, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.createSetup()
        self.onLayoutFinish.append(self.layoutFinished)
        if self.setInfo not in self['config'].onSelectionChanged:
            self['config'].onSelectionChanged.append(self.setInfo)

    def layoutFinished(self):
        payp = paypal()
        self["paypal"].setText(payp)
        self.setTitle(self.setup_title)
        if not os.path.exists('/tmp/currentip'):
            os.system('wget -qO- http://ipecho.net/plain > /tmp/currentip')
        currentip1 = open('/tmp/currentip', 'r')
        currentip = currentip1.read()
        self['info'].setText(_('Settings FILMXY\nYour current IP is %s') % currentip)

    def createSetup(self):
        self.editListEntry = None
        self.list = []
        self.list.append(getConfigListEntry(_("Set the path Movie folder"), config.plugins.filmxy.movie, _("Folder Movie Path (eg.: /media/hdd/movie), Press OK - Enigma restart required")))
        self.list.append(getConfigListEntry(_("Set the path to the Cache folder"), config.plugins.filmxy.cachefold, _("Press Ok to select the folder containing the picons files")))
        self.list.append(getConfigListEntry(_('Services Player Reference type'), config.plugins.filmxy.services, _("Configure Service Player Reference")))
        self.list.append(getConfigListEntry(_('Force Services Player Reference type'), config.plugins.filmxy.servicesforce, _("Force Service Player Reference")))
        self["config"].list = self.list
        self["config"].l.setList(self.list)
        # self.setInfo()

    def setInfo(self):
        try:
            sel = self['config'].getCurrent()[2]
            if sel:
                # print('sel =: ', sel)
                self['description'].setText(str(sel))
            else:
                self['description'].setText(_('SELECT YOUR CHOICE'))
            return
        except Exception as e:
            print("Error ", e)

    def cachedel(self):
        fold = config.plugins.filmxy.cachefold.value  # + "/pic"
        cmd = "rm " + fold + "/*"
        os.system(cmd)
        self.mbox = self.session.open(MessageBox, _('All cache fold are empty!'), MessageBox.TYPE_INFO, timeout=5)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        logdata("current selection:", self["config"].l.getCurrentSelection())
        self.createSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        logdata("current selection:", self["config"].l.getCurrentSelection())
        self.createSetup()

    def msgok(self):
        if self['config'].isChanged():
            for x in self['config'].list:
                x[1].save()
            self.mbox = self.session.open(MessageBox, _('Settings saved correctly!'), MessageBox.TYPE_INFO, timeout=5)
            self.close()
        else:
            self.close()

    def Ok_edit(self):
        ConfigListScreen.keyOK(self)
        sel = self['config'].getCurrent()[1]
        if sel and sel == config.plugins.filmxy.cachefold:
            self.setting = 'cachefold'
            mmkpth = config.plugins.filmxy.cachefold.value
            self.openDirectoryBrowser(mmkpth)
        if sel and sel == config.plugins.filmxy.movie:
            self.setting = 'moviefold'
            self.openDirectoryBrowser(config.plugins.filmxy.movie.value)
        else:
            pass

    def openDirectoryBrowser(self, path):
        try:
            self.session.openWithCallback(
             self.openDirectoryBrowserCB,
             LocationBox,
             windowTitle=_('Choose Directory:'),
             text=_('Choose Directory'),
             currDir=str(path),
             bookmarks=config.movielist.videodirs,
             autoAdd=False,
             editDir=True,
             inhibitDirs=['/bin', '/boot', '/dev', '/home', '/lib', '/proc', '/run', '/sbin', '/sys', '/var'],
             minFree=15)
        except Exception as e:
            print('openDirectoryBrowser get failed: ', e)

    def openDirectoryBrowserCB(self, path):
        if path is not None:
            if self.setting == 'cachefold':
                config.plugins.filmxy.cachefold.setValue(path)
            if self.setting == 'moviefold':
                config.plugins.filmxy.movie.setValue(path)
        return

    def KeyText(self):
        sel = self['config'].getCurrent()
        if sel:
            from Screens.VirtualKeyBoard import VirtualKeyBoard
            self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self['config'].getCurrent()[0], text=self['config'].getCurrent()[1].value)

    def VirtualKeyBoardCallback(self, callback=None):
        if callback is not None and len(callback):
            self['config'].getCurrent()[1].value = callback
            self['config'].invalidate(self['config'].getCurrent())
        return

    def restartenigma(self, result):
        if result:
            self.session.open(TryQuitMainloop, 3)
        else:
            self.close(True)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()
        try:
            if isinstance(self['config'].getCurrent()[1], ConfigEnableDisable) or isinstance(self['config'].getCurrent()[1], ConfigYesNo) or isinstance(self['config'].getCurrent()[1], ConfigSelection):
                self.createSetup()
        except:
            pass

    def getCurrentEntry(self):
        return self['config'].getCurrent() and self['config'].getCurrent()[0] or ''

    def getCurrentValue(self):
        return self['config'].getCurrent() and str(self['config'].getCurrent()[1].getText()) or ''

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def extnok(self):
        if self['config'].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _('Really close without saving the settings?'))
        else:
            self.close()

    def cancelConfirm(self, result):
        if not result:
            return
        for x in self['config'].list:
            x[1].cancel()
        self.close()


class StreamTasks(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        skin = os.path.join(skin_path, 'StreamTasks.xml')
        with open(skin, 'r') as f:
            self.skin = f.read()
        self.setup_title = ('Filmxy Movies')
        from Components.Sources.List import List
        self["movielist"] = List([])
        self["key_green"] = Label(_("Remove"))
        self["key_red"] = Label(_("Close"))
        self["actions"] = ActionMap(["OkCancelActions",
                                     "SleepTimerEditorActions",
                                     "ColorActions"], {
                                                       "ok": self.keyOK,
                                                       "esc": self.keyClose,
                                                       "exit": self.keyClose,
                                                       "green": self.message1,
                                                       "red": self.keyClose,
                                                       "blue": self.keyBlue,
                                                       "cancel": self.keyClose}, -1)
        self.initialservice = self.session.nav.getCurrentlyPlayingServiceReference()
        self.Timer = eTimer()
        try:
            self.Timer_conn = self.Timer.timeout.connect(self.TimerFire)
        except:
            self.Timer.callback.append(self.TimerFire)
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.__onClose)

    def __onClose(self):
        del self.Timer

    def layoutFinished(self):
        self.Timer.startLongTimer(2)

    def TimerFire(self):
        self.Timer.stop()
        self.rebuildMovieList()

    def rebuildMovieList(self):
        if os.path.exists(Path_Movies):
            self.movielist = []
            self.getTaskList()
            self.getMovieList()
            self["movielist"].setList(self.movielist)
            self["movielist"].updateList(self.movielist)
        else:
            message = "The Movie path not configured or path not exist!!!"
            Utils.web_info(message)
            self.close()

    def getTaskList(self):
        jobs = job_manager.getPendingJobs()
        if len(jobs) >= 1:
            for job in jobs:
                jobname = str(job.name)
                self.movielist.append((
                    job,
                    jobname,
                    job.getStatustext(),
                    int(100 * float(job.progress) / float(job.end)),
                    str(100 * float(job.progress) / float(job.end)) + "%"))
            if len(self.movielist) >= 1:
                self.Timer.startLongTimer(10)
        return

    def getMovieList(self):
        global filelist, file1
        filelist = ''
        file1 = False
        self.pth = ''
        if os.path.isdir(Path_Movies):
            filelist = os.listdir(Path_Movies)
        path = Path_Movies

        if filelist is not None:
            file1 = True
            filelist.sort()
            for filename in filelist:
                if os.path.exists(path + filename):
                    if filename.endswith(".meta"):
                        continue
                    if ".m3u" in filename:
                        continue
                    if "autotimer" in filename:
                        continue
                self.movielist.append(("movie", filename, _("Finished"), 100, "100%"))

    def keyOK(self):
        global file1
        current = self["movielist"].getCurrent()
        path = Path_Movies
        if current:
            if current[0] == "movie":
                if file1 is True:
                    path = Path_Movies
                url = path + current[1]
                name = current[1]
                file1 = False
                isFile = os.path.exists(url)
                if isFile:
                    self.session.open(Playstream2, name, url)
                else:
                    self.session.open(MessageBox, _("Is Directory or file not exist"), MessageBox.TYPE_INFO, timeout=5)
            else:
                job = current[0]
                self.session.openWithCallback(self.JobViewCB, JobView, job)

    def keyBlue(self):
        pass

    def JobViewCB(self, why):
        pass

    def keyClose(self):
        self.close()

    def message1(self):
        current = self["movielist"].getCurrent()
        sel = Path_Movies + current[1]
        dom = sel
        self.session.openWithCallback(self.callMyMsg1, MessageBox, _("Do you want to remove %s ?") % dom, MessageBox.TYPE_YESNO, timeout=15, default=False)

    def callMyMsg1(self, result):
        if result:
            current = self["movielist"].getCurrent()
            sel = Path_Movies + current[1]
            from os.path import exists as file_exists
            if file_exists(sel):
                if self.Timer:
                    self.Timer.stop()
                cmd = 'rm -f ' + sel
                os.system(cmd)
                self.session.open(MessageBox, sel + _("Movie has been successfully deleted\nwait time to refresh the list..."), MessageBox.TYPE_INFO, timeout=5)
            else:
                self.session.open(MessageBox, _("The movie not exist!\nwait time to refresh the list..."), MessageBox.TYPE_INFO, timeout=5)
            self.onShown.append(self.rebuildMovieList)


class downloadJob(Job):
    def __init__(self, toolbox, cmdline, filename, filmtitle):
        Job.__init__(self, filmtitle)
        self.cmdline = cmdline
        self.filename = filename
        self.toolbox = toolbox
        self.retrycount = 0
        downloadTask(self, cmdline, filename, filmtitle)

    def retry(self):
        assert self.status == self.FAILED
        self.restart()

    def cancel(self):
        self.abort()


class downloadTaskPostcondition(Condition):
    RECOVERABLE = True

    def check(self, task):
        if task.returncode == 0 or task.error is None:
            return True
        else:
            return False
            return

    def getErrorMessage(self, task):
        return {
            task.ERROR_CORRUPT_FILE: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("DOWNLOADED FILE CORRUPTED:") + '\n%s' % task.lasterrormsg,
            task.ERROR_RTMP_ReadPacket: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("COULD NOT READ RTMP PACKET:") + '\n%s' % task.lasterrormsg,
            task.ERROR_SEGFAULT: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("SEGMENTATION FAULT:") + '\n%s' % task.lasterrormsg,
            task.ERROR_SERVER: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("SERVER RETURNED ERROR:") + '\n%s' % task.lasterrormsg,
            task.ERROR_UNKNOWN: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("UNKNOWN ERROR:") + '\n%s' % task.lasterrormsg
        }[task.error]


class downloadTask(Task):
    if PY3:
        ERROR_CORRUPT_FILE, ERROR_RTMP_ReadPacket, ERROR_SEGFAULT, ERROR_SERVER, ERROR_UNKNOWN = list(range(5))
    else:
        ERROR_CORRUPT_FILE, ERROR_RTMP_ReadPacket, ERROR_SEGFAULT, ERROR_SERVER, ERROR_UNKNOWN = range(5)

    def __init__(self, job, cmdline, filename, filmtitle):
        Task.__init__(self, job, "Downloading ..." + filmtitle)
        self.toolbox = job.toolbox
        self.setCmdline(cmdline)
        self.filename = filename
        self.filmtitle = filmtitle
        self.error = None
        self.lasterrormsg = None
        self.progress = 0
        self.lastprogress = 0
        self.firstrun = True
        self.starttime = time.time()

    def processOutput(self, data):
        global ui
        if PY3:
            data = str(data)
        try:
            if data.find("%") != -1:
                tmpvalue = re.findall(r'(\d+?%)', data)[-1].rstrip("%")
                self.progress = int(float(tmpvalue))

                if self.firstrun:
                    self.firstrun = False
                    if ui:
                        self.toolbox.updatescreen()

                elif self.progress == 100:
                    self.lastprogress = int(self.progress)
                    if ui:
                        self.toolbox.updatescreen()

                elif int(self.progress) != int(self.lastprogress):
                    self.lastprogress = int(self.progress)

                    elapsed_time = time.time() - self.starttime
                    if ui and elapsed_time > 2:
                        self.starttime = time.time()
                        self.toolbox.updatescreen()
                else:
                    Task.processOutput(self, data)

        except Exception as errormsg:
            print("Error processOutput: " + str(errormsg))
            Task.processOutput(self, data)

    def processOutputLine(self, line):
        pass

    def afterRun(self):
        if self.getProgress() == 100 or self.progress == 100:
            try:
                self.toolbox.download_finished(self.filename, self.filmtitle)
            except Exception as e:
                print(e)


class AutoStartTimerFxy:

    def __init__(self, session):
        self.session = session
        global _firstStart
        logdata("*** running AutoStartTimerFxy ***")
        if _firstStart:
            self.runUpdate()

    def runUpdate(self):
        logdata("*** running update ***")
        try:
            from . import Update
            Update.upd_done()
            _firstStart = False
        except Exception as e:
            logdata('error Fxy', e)


def autostart(reason, session=None, **kwargs):
    logdata("*** running autostart ***")
    global autoStartTimerFxy
    global _firstStart
    if reason == 0:
        if session is not None:
            _firstStart = True
            autoStartTimerFxy = AutoStartTimerFxy(session)
    return


def main(session, **kwargs):
    try:
        session.open(Filmxymain)
    except:
        import traceback
        traceback.print_exc()


def menu(menuid, **kwargs):
    if menuid == 'mainmenu':
        return [(desc_plug, main, title_plug, 44)]
    else:
        return []


def mainmenu(session, **kwargs):
    main(session, **kwargs)


def Plugins(**kwargs):
    ico_path = 'logo.png'
    if not os.path.exists('/var/lib/dpkg/status'):
        ico_path = res_plugin_path + 'pics/logo.png'
    result = [PluginDescriptor(name=desc_plug, description=title_plug, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
              PluginDescriptor(name=desc_plug, description=title_plug, where=PluginDescriptor.WHERE_PLUGINMENU, icon=ico_path, fnc=main)]
    return result
