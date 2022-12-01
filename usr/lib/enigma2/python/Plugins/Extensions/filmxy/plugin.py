#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
****************************************
*        coded by Lululla              *
*        Many thank's Pcd              *
*             10/10/2022               *
*       skin by MMark                  *
****************************************
Info http://t.me/tivustream
'''
from __future__ import print_function
from . import Utils
from . import html_conv
from . import _
from Components.AVSwitch import AVSwitch
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
from Components.config import getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
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
from os.path import splitext
from twisted.web.client import downloadPage
import os
import random
import re
import six
import ssl
import sys
import time
PY3 = False
PY3 = sys.version_info.major >= 3
print('Py3: ', PY3)
if PY3:
    print('six.PY3: True ')
# from six.moves.urllib.parse import urljoin, unquote_plus, quote_plus, quote, unquote

try:
    from urllib.parse import urlparse
    from urllib.parse import unquote
    from urllib.error import URLError
    # from urllib.request import urlretrieve
    # from urllib.request import urlopen
    PY3 = True
    # unicode = str
    # unichr = chr
    # long = int
except ImportError:
    from urlparse import urlparse
    from urllib import unquote
    from urllib2 import URLError
    # from urllib import urlretrieve
    # from urllib2 import Request
    # from urllib2 import urlopen
    

# if sys.version_info.major == 3:
	 # import urllib.request as urllib2
# elif sys.version_info.major == 2:
	 # import urllib2


plugin_path = os.path.dirname(sys.modules[__name__].__file__)
global skin_path, cachefold, pngs, nextmodule, pictmp, Path_Movies

_session = None
_firstStart = True
Host = "https://www.filmxy.pw/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'Accept-Encoding': 'deflate'}

streamlink = False
if Utils.isStreamlinkAvailable:
    streamlink = True


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


def getversioninfo():
    currversion = '1.7'
    version_file = plugin_path + '/version'
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
cfg = config.plugins.filmxy


Path_Movies = str(config.plugins.filmxy.movie.value)
if Path_Movies.endswith("\/\/"):
    Path_Movies = Path_Movies[:-1]
print('patch movies: ', Path_Movies)

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
cachefold = config.plugins.filmxy.cachefold.value.strip()
pictmp = cachefold + "/poster.jpg"
pmovies = False

if cachefold.endswith('\/\/'):
    cachefold = cachefold[:-1]
if not os.path.exists(cachefold):
    try:
        os.makedirs(cachefold)
    except OSError as e:
        print(('Error creating directory %s:\n%s') % (cachefold, str(e)))
logdata("path cachefold: ", str(cachefold))


if Utils.isFHD():
    skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/skins/fhd/".format('filmxy'))
else:
    skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/res/skins/hd/".format('filmxy'))

if Utils.DreamOS():
    skin_path = skin_path + 'dreamOs/'
logdata("path skin_path: ", str(skin_path))


def returnIMDB(text_clear):
    if Utils.is_tmdb:
        try:
            from Plugins.Extensions.TMBD.plugin import TMBD
            text = html_conv.html_unescape(text_clear)
            _session.open(TMBD.tmdbScreen, text, 0)
        except Exception as ex:
            print("[XCF] Tmdb: ", str(ex))
        return True
    elif Utils.is_imdb:
        try:
            from Plugins.Extensions.IMDb.plugin import main as imdb
            text = html_conv.html_unescape(text_clear)
            imdb(_session, text)
        except Exception as ex:
            print("[XCF] imdb: ", str(ex))
        return True
    else:
        text_clear = html_conv.html_unescape(text_clear)
        _session.open(MessageBox, text_clear, MessageBox.TYPE_INFO)
        return True
    return


status = True


def status_site():
    global status
    import requests
    url = 'https://www.filmxy.pw/movie-list'
    response = requests.get(url)
    if response.status_code == 200:
        status = True
        print('Web site exists')
        return True
    else:
        status = False
        print('Web site does not exist')
        return False
    return


def piconlocal(name):
    picolocal = 'backg2.png'
    if 'tv' in name.lower():
        picolocal = 'movie.png'
    elif 'adult' in name.lower():
        picolocal = 'adult.png'
    elif 'animation' in name.lower():
        picolocal = 'animation.png'
    elif 'biography' in name.lower():
        picolocal = 'biography.png'
    elif 'show' in name.lower():
        picolocal = 'game-show.png'
    elif 'history' in name.lower():
        picolocal = 'history.png'
    elif 'music' in name.lower():
        picolocal = 'music.png'
    elif 'sci-fi' in name.lower():
        picolocal = 'sci-fi.png'
    elif 'family' in name.lower():
        picolocal = 'family.png'
    elif 'short' in name.lower():
        picolocal = 'short.png'
    elif 'uncategorized' in name.lower():
        picolocal = 'uncategorized.png'
    elif 'war' in name.lower():
        picolocal = 'war.png'
    elif 'commedia' in name.lower():
        picolocal = 'commedia.png'
    elif 'comedy' in name.lower():
        picolocal = 'commedia.png'
    elif 'thriller' in name.lower():
        picolocal = 'thriller.png'
    elif 'azione' in name.lower():
        picolocal = 'azione.png'
    elif 'dramma' in name.lower():
        picolocal = 'dramma.png'
    elif 'drama' in name.lower():
        picolocal = 'dramma.png'
    elif 'western' in name.lower():
        picolocal = 'western.png'
    elif 'biografico' in name.lower():
        picolocal = 'biografico.png'
    elif 'romantico' in name.lower():
        picolocal = 'romantico.png'
    elif 'romance' in name.lower():
        picolocal = 'romantico.png'
    elif 'horror' in name.lower():
        picolocal = 'horror.png'
    elif 'musica' in name.lower():
        picolocal = 'musical.png'
    elif 'guerra' in name.lower():
        picolocal = 'guerra.png'
    elif 'bambini' in name.lower():
        picolocal = 'bambini.png'
    elif 'bianco' in name.lower():
        picolocal = 'bianconero.png'
    elif 'tutto' in name.lower():
        picolocal = 'toto.png'
    elif 'cartoni' in name.lower():
        picolocal = 'cartoni.png'
    elif 'bud' in name.lower():
        picolocal = 'budterence.png'
    elif 'documentary' in name.lower():
        picolocal = 'documentary.png'
    elif 'crime' in name.lower():
        picolocal = 'crime.png'
    elif 'mystery' in name.lower():
        picolocal = 'mistery.png'
    elif 'fiction' in name.lower():
        picolocal = 'fiction.png'
    elif 'adventure' in name.lower():
        picolocal = 'mistery.png'
    elif 'action' in name.lower():
        picolocal = 'azione.png'
    elif '007' in name.lower():
        picolocal = '007.png'
    elif 'sport' in name.lower():
        picolocal = 'sport.png'
    elif 'teatr' in name.lower():
        picolocal = 'teatro.png'
    elif 'extra' in name.lower():
        picolocal = 'extra.png'
    elif 'search' in name.lower():
        picolocal = 'search.png'
    elif 'mediaset' in name.lower():
        picolocal = 'mediaset.png'
    elif 'nazionali' in name.lower():
        picolocal = 'nazionali.png'
    elif 'news' in name.lower():
        picolocal = 'news.png'
    elif 'rai' in name.lower():
        picolocal = 'rai.png'
    elif 'webcam' in name.lower():
        picolocal = 'relaxweb.png'
    elif 'relax' in name.lower():
        picolocal = 'relaxweb.png'
    elif 'vecchi' in name.lower():
        picolocal = 'vecchi.png'
    elif 'italia' in name.lower():
        picolocal = 'movie.png'
    elif 'fantascienza' in name.lower():
        picolocal = 'fantascienza.png'
    elif 'fantasy' in name.lower():
        picolocal = 'fantasy.png'
    elif 'fantasia' in name.lower():
        picolocal = 'fantasia.png'
    elif 'film' in name.lower():
        picolocal = 'movie.png'
    elif 'plutotv' in name.lower():
        picolocal = 'plutotv.png'
    elif 'samsung' in name.lower():
        picolocal = 'samsung.png'
    elif 'prev' in name.lower():
        picolocal = prevpng
    elif 'next' in name.lower():
        picolocal = nextpng
    print('>>>>>>>> ' + str(piccons) + str(picolocal))
    name = str(piccons) + str(picolocal)
    return name


class rvList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)
        if Utils.isFHD():
            self.l.setItemHeight(54)
            textfont = int(34)
            self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(54)
            textfont = int(24)
            self.l.setFont(0, gFont('Regular', textfont))


def rvListEntry(name, idx):
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
    if Utils.isFHD():
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 0), size=(50, 50), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(90, 0), size=(1900, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
    else:
        res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 0), size=(50, 50), png=loadPNG(pngs)))
        res.append(MultiContentEntryText(pos=(90, 0), size=(1000, 50), font=0, text=name, color=0xa6d1fe, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER))
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
        global _session
        _session = session
        skin = skin_path + 'Filmxymain.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        global nextmodule
        nextmodule = 'Filmxymain'
        self['list'] = rvList([])
        self.setup_title = ('HOME FILMXY')
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
        self.scale = AVSwitch().getFramebufferScale()
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
            print('error showIMDB ', str(e))

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
        # Utils.deletetmp()
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
        print('iiiiii= ', i)
        if i < 1:
            return

        # if status is True:
        global nextmodule
        sel = self.menu_list[idx]
        if sel == ('CATEGORIES'):
            name = 'CATEGORIES'
            url = Host
            pic = piconmovie
            nextmodule = 'categories'
            logdata("Filmxymain nextmodule: ", nextmodule)
            self.session.open(live_to_stream, name, url, pic, nextmodule)
        elif sel == ('COUNTRIES'):
            name = 'COUNTRIES'
            url = Host
            pic = piconinter
            nextmodule = 'countries'
            logdata("Filmxymain nextmodule: ", nextmodule)
            self.session.open(live_to_stream, name, url, pic, nextmodule)
        elif sel == 'YEARS':
            name = 'YEARS'
            url = Host
            pic = piconold
            nextmodule = 'years'
            logdata("Filmxymain nextmodule: ", nextmodule)
            self.session.open(live_to_stream, name, url, pic, nextmodule)
        elif sel == ('A-Z'):
            name = 'A-Z'
            url = Host
            pic = piconsearch
            nextmodule = 'az'
            logdata("Filmxymain nextmodule: ", nextmodule)
            self.session.open(live_to_stream, name, url, pic, nextmodule)
        else:
            if sel == ('INTERNATIONAL'):
                logdata("Filmxymain nextmodule: ", 'INTERNATIONAL')
                self.zfreearhey()

    def zfreearhey(self):
        freearhey = resolveFilename(SCOPE_PLUGINS, "Extensions/{}/skin".format('freearhey'))
        if os.path.isdir(freearhey):
            from Plugins.Extensions.freearhey.plugin import freearhey
            self.session.open(freearhey)
        else:
            try:
                self.mbox = self.session.open(MessageBox, _('freearhey Plugin Not Installed!!\nUse my Plugin Freearhey'), MessageBox.TYPE_INFO, timeout=4)
            except Exception as e:
                print('error infobox ', str(e))

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
                self.scale = AVSwitch().getFramebufferScale()
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
                else:
                    print('no cover.. error')
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Playchoice")
        return


class live_to_stream(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'Filmxymain.xml'
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
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.next = nextmodule
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
        self.readJsonTimer.start(500, True)
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.left)
        except:
            self.leftt.callback.append(self.left)
        self.leftt.start(1000, True)
        self.onLayoutFinish.append(self.__layoutFinished)
        # self.currentList.moveToIndex(0)

    def showIMDB(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                print('show imdb/tmdb')
        except Exception as ex:
            print(str(ex))
            print("Error: can't find showIMDB in live_to_stream")

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        try:
            if 'categories' in self.next:
                content = Utils.ReadUrl(Host)
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
                        self.downloadPic(None, pixmaps)
                        pic = pixmaps
                    else:
                        pic = no_cover
                    print('name categories', name)
                    print('url categories', url)
                    self.names.append(name)
                    self.urls.append(url)
                    self.pics.append(pic)
                    self.infos.append(self.next)
            elif 'countries' in self.next:
                content = Utils.ReadUrl(Host)
                n1 = content.find("var country=", 0)
                n2 = content.find("</script>", n1)
                content2 = content[n1:n2]
                regexvideo = 'name:"(.*?)",link:"(.*?)"'
                match = re.compile(regexvideo, re.DOTALL).findall(content2)
                for name, url in match:
                    print('name country', name)
                    print('url country', url)
                    pixmaps = piconlocal(name)
                    if os.path.exists(pixmaps):
                        self.downloadPic(None, pixmaps)
                        pic = pixmaps
                    else:
                        pic = no_cover
                    self.names.append(name)
                    self.urls.append(url)
                    self.pics.append(pic)
                    self.infos.append(self.next)
            elif 'years' in self.next:
                content = Utils.ReadUrl(Host)
                n1 = content.find("var years=", 0)
                n2 = content.find("var country", n1)
                content2 = content[n1:n2]
                regexvideo = 'name:"(.*?)",link:"(.*?)"'
                match = re.compile(regexvideo, re.DOTALL).findall(content2)
                for name, url in match:
                    pixmaps = piconlocal(name)
                    if os.path.exists(pixmaps):
                        self.downloadPic(None, pixmaps)
                        pic = pixmaps
                    else:
                        pic = no_cover
                    print('name years', name)
                    print('url years', url)

                    self.names.append(name)
                    self.urls.append(url)
                    self.pics.append(pic)
                    self.infos.append(self.next)
            elif 'az' in self.next:
                content = Utils.ReadUrl(Host)
                n1 = content.find('class="numeric-pagination post-list"><ul>', 0)
                n2 = content.find("/div><div", n1)
                content2 = content[n1:n2]
                regexvideo = 'https://www.filmxy.pw/movie-list/(.*?)/.*?>(.*?)<'
                match = re.compile(regexvideo, re.DOTALL).findall(content2)
                for url, name in match:
                    url1 = "https://www.filmxy.pw/movie-list/" + url + "/"
                    pixmaps = piconlocal(name)
                    if os.path.exists(pixmaps):
                        self.downloadPic(None, pixmaps)
                        pic = pixmaps
                    else:
                        pic = no_cover
                    print('name az', name)
                    print('url az', url)
                    self.names.append(name)
                    self.urls.append(url1)
                    self.pics.append(pic)
                    self.infos.append(self.next)
            logdata("live_to_stream self.next: ", self.next)
            showlist(self.names, self['list'])
            # self['list'].moveToIndex(0)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in live_to_stream")
        return

    def okRun(self):
        i = len(self.names)
        print('iiiiii= ', i)
        if i < 1:
            return
        try:
            idx = self['list'].getSelectionIndex()
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            # pages
            if nextmodule == 'countries':
                print('pages next: ', nextmodule)
                self.session.open(pagesX, name, url, pic, nextmodule)
                return
            elif nextmodule == 'categories':
                print('pages next: ', nextmodule)
                self.session.open(pagesX, name, url, pic, nextmodule)
                return
            elif nextmodule == 'years':
                print('pages next: ', nextmodule)
                self.session.open(pagesX, name, url, pic, nextmodule)
                return
            # az
            elif nextmodule == 'az':
                print('az next: ', nextmodule)
                self.session.open(azvideo, name, url, pic, nextmodule)
                return
        except Exception as ex:
            print(str(ex))
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
        i = len(self.names)
        print('iiiiii= ', i)
        if i > 0:
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)

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
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            pixmaps = self.pics[idx]
            print('pixmap  : ', pixmaps)
            if str(res_plugin_path) in pixmaps:
                self.downloadPic(None, pixmaps)
                return
            # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    # print("debug pixmaps t:", pixmaps)
                    # print("debug pixmaps t:", type(pixmaps))
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as ex:
                    print(str(ex))
                    print("Error: can't find file or read data live_to_stream")
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Playchoice")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
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


class pagesX(Screen):
    def __init__(self, session, name, url, pic, nextmodule):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'Filmxymain.xml'
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
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.next = nextmodule
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
        # self.load_infos()
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
                # name = name.upper()
                print('name pagesX: ', name)
                print('url pagesX: ', url1)
                info = self.name
                self.names.append(name)
                self.urls.append(url1)
                pic = self.pic
                self.pics.append(pic)
                self.infos.append(info)
            logdata("pages nextmodule: ", self.next)
            showlist(self.names, self['list'])
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in pagesX")
        return

    def okRun(self):
        i = len(self.pics)
        print('iiiiii= ', i)
        if i < 1:
            return
        try:
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            # desc = self.infos[idx]
            print('name okRun pagesX: ', name)
            print('url okRun pagesX: ', url)
            logdata("pages nextmodule: ", self.next)
            self.session.open(pagevideo3, name, url, pic, self.next)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in pagesX")

    def cancel(self):
        self.close(None)

    def up(self):
        self[self.currentList].up()
        # self.load_poster()

    def down(self):
        self[self.currentList].down()
        # self.load_poster()

    def left(self):
        self[self.currentList].pageUp()
        # self.load_poster()

    def right(self):
        self[self.currentList].pageDown()
        # self.load_poster()

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
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
        skin = skin_path + 'Filmxymain.xml'
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
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.next = nextmodule
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
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                print('show imdb/tmdb')
        except Exception as ex:
            print(str(ex))
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
        i = len(self.names)
        print('load infos azvideo ', i)
        if i > 0:
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            # info = html_conv.html_unescape(info)
            self['desc'].setText(info)

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl(self.url)
        if PY3:
            content = six.ensure_str(content)
        print("azvideo content A =", content)
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
                print('azvideo name ', name)
                print('azvideo url ', url)
                # print('azvideo pic ' , pic)
                # print('azvideo info ' , info)
                url1 = url + "/"
                pixmaps = piconlocal(name)
                if os.path.exists(pixmaps):
                    self.downloadPic(None, pixmaps)
                    pic = pixmaps
                else:
                    pic = no_cover
                self.names.append(name)
                self.urls.append(url1)
                self.pics.append(pic)
                self.infos.append(self.next)
            logdata("azvideo nextmodule: ", self.next)
            showlist(self.names, self['list'])
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in azvideo")

    def okRun(self):
        i = len(self.names)
        print('okrun azvideo ', i)
        if i < 1:
            return
        try:
            idx = self['list'].getSelectionIndex()
            print('azvideo idx: ', idx)
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            desc = self.infos[idx]
            # self.next = desc
            logdata("azvideo name: ", name)
            self.session.open(Video5list, name, url, pic, desc)
        except Exception as ex:
            print(str(ex))
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
            print('azvideo loadposter ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
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
                except Exception as ex:
                    print(str(ex))
                    print("Error: can't find file in azvideo")
            return
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Playchoice")

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
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
        skin = skin_path + 'Filmxymain.xml'
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
        self.scale = AVSwitch().getFramebufferScale()
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
        self.next = nextmodule
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
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                print('show imdb/tmdb')
        except Exception as ex:
            print(str(ex))
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
        # self.load_infos()
        # self.load_poster()

    def load_infos(self):
        try:
            i = len(self.names)
            print('iiiiii=pagevideo3 ', i)
            if i > 0:
                idx = self['list'].getSelectionIndex()
                infoadd = self.infosadd[idx]
                size2 = self.sizes[idx]
                info = self.infos[idx]
                info = html_conv.html_unescape(info)
                intot = str(infoadd) + '\n' + str(size2)
                print('intot = ', intot)
                print('info = ', info)
                # self['desc'].setText(info + '\n' + 'Stream N.' + str(i))
                self['desc'].setText(info)
                self['descadd'].setText(intot)
            return
        except Exception as ex:
            print(str(ex))
            print("Error: can't find pagevideo3 in load_infos")

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
        content = Utils.ReadUrl(self.url)
        if PY3:
            content = six.ensure_str(content)
        print("content pagevideo3 =", content)
        try:

            # <div
            # class="col-md-2 col-sm-3 col-xs-6 custom-col"><div
            # class=single-post><div
            # class=post-thumbnail>
            # <a
            # href=https://www.filmxy.pw/the-quiet-2005/ >
            # <img
            # width=250 height=350 data-src=https://www.cdnzone.org/uploads/2022/11/04/The-Quiet-2005-Cover.jpg src=https://www.cdnzone.org/asset/images/1px.png alt="The Quiet Cover">
            # </a><div
            # class="m-type post">Movie</div><div
            # class="m-quality green">HD/Web-DL</div></div><div
            # class=post-description><div
            # class=post-title><h2>The Quiet (2005)</h2></div><div
            # class=imdb-details><p><b>IMDb: </b>6.2/10</p></div><div
            # class=available-quality><p>720p | 1080p</p></div><div
            # class=genre><p><b>Ganre: </b>Crime, Drama, Thriller</p></div><div
            # class=mpa><p><b>MPA: </b>R</p></div><div
            # class=size><p><b>Size: </b>883.62 MB | 1.6 GB</p></div><div
            # class=story><p>This film receives a 10 for disturbing subject matter. It is at times very difficult to watch. The characters are troubled, each in his/her own way. It feels edgy and often very foreign. With that warning, I must say that on some level I enjoyed the film. Technically it is superb. The character development is [&hellip;]</p></div><div

            # class=story></div><div

            # class=categories><p><b>Category: </b> <a
            # href=https://www.filmxy.pw/genre/adult/ rel="category tag">Adult</a>, <a
            # href=https://www.filmxy.pw/genre/crime/ rel="category tag">Crime</a>, <a
            # href=https://www.filmxy.pw/genre/drama/ rel="category tag">Drama</a>, <a
            # href=https://www.filmxy.pw/genre/thriller/ rel="category tag">Thriller</a></p></div></div></div></div><div

            # regexvideo = 'class=post-thumbnail>.*?href=(.*?)/ >.*?data-src=(.*?) src.*?title><h2>(.*?)<'

            # class=single-post><div
            # class=post-thumbnail>
            # <a
            # href=https://www.filmxy.pw/route-10-2022/ >
            # <img
            # width=250 height=350 data-src=https://www.cdnzone.org/uploads/2022/10/30/Route-10-2022-Cover.jpg src=https://www.cdnzone.org/asset/images/1px.png alt="Route 10 Cover">
            # </a><div
            # class="m-type post">Movie</div><div
            # class="m-quality green">HD/Web-DL</div></div><div
            # class=post-description><div
            # class=post-title><h2>Route 10 (2022)</h2></div><div
            # class=imdb-details><p><b>IMDb: </b>6.1/10</p></div><div
            # class=available-quality><p>720p | 1080p</p></div><div
            # class=genre><p><b>Ganre: </b>Action, Drama, Thriller</p></div><div
            # class=mpa><p><b>MPA: </b>N/A</p></div><div
            # class=size><p><b>Size: </b>749.68 MB | 1.5 GB</p></div><div
            # class=story></div><div
            # class=categories><p><b>Category: </b> <a
            # href=https://www.filmxy.pw/genre/action/ rel="category tag">Action</a>, <a
            # href=https://www.filmxy.pw/genre/drama/ rel="category tag">Drama</a>, <a
            # href=https://www.filmxy.pw/genre/thriller/ rel="category tag">Thriller</a></p></div></div></div></div><div

            # n1 = content.find("cat-description", 0)
            # n2 = content.find("numeric-pagination>", n1)
            # content2 = content[n1:n2]
            # regexvideo = 'post-thumbnail>.*?href=(.*?)>.*?data-src=(.*?)src.*?title><h2>(.*?)<.*?Ganre:.*?</b>(.*?)</p>.*?Size:.*?</b>(.*?)</p>.*?story><p>(.*?)</p>'
            regexvideo = 'post-thumbnail>.*?href=(.*?)>.*?data-src=(.*?)src.*?title><h2>(.*?)<.*?Ganre:.*?</b>(.*?)</p>.*?Size:.*?(.*?)</p>.*?story>(.*?)</div>'
            match = re.compile(regexvideo, re.DOTALL).findall(content)
            for url, pic, name, infoadd, size, info in match:
                url1 = url.replace(' ', '')
                url1 = url1.strip()  # + "/"
                pic = pic.strip()
                name = name.strip()
                # name = name.replace("-Cover", "").replace(" Cover", "")
                name = html_conv.html_unescape(name)
                size = size.replace('</b>', '').replace(' ', '')
                size2 = 'Size ' + str(size)
                info = info.replace('<p>', '').replace('</p>', '').replace('&hellip;', '...')
                print('pagevideo3 url ', url)
                print('pagevideo3 pic ', pic)
                print('pagevideo3 name ', name)
                print('pagevideo3 infoadd ', infoadd)
                print('pagevideo3 size ', size)
                print('pagevideo3 info ', info)
                self.urls.append(url1)
                self.pics.append(pic)
                self.names.append(name)
                self.infosadd.append(infoadd)
                self.sizes.append(size2)
                self.infos.append(info)
            logdata("pagevideo3 nextmodule: ", self.next)
            showlist(self.names, self['list'])
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in pagevideo3")
        return

    def okRun(self):
        # idx = self['list'].getSelectionIndex()
        # print('idx: ', idx)
        # if idx and (idx != '' or idx > -1):
        try:
            idx = self['list'].getSelectionIndex()
            print('video4 idx: ', idx)
            name = self.names[idx]
            url = self.urls[idx]
            pic = self.pics[idx]
            info = self.infos[idx]
            logdata("pagevideo3 name: ", name)
            self.session.open(Video5list, name, url, pic, info)
        except Exception as ex:
            print(str(ex))
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
            print('loadposter pagevideo3 ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('load_poster idx: ', idx)
            # name = self.names[idx]
            # url = self.urls[idx]
            pixmaps = self.pics[idx]
            # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    # print("debug pixmaps x:", pixmaps)
                    # print("debug pixmaps x:", type(pixmaps))
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as ex:
                    print(str(ex))
                    print("Error: can't find file in pagevideo3")
        except Exception as ex:
            print(str(ex))
            print("Error: pagevideo3")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
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


class Video5list(Screen):
    def __init__(self, session, name, url, pic, info):
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        skin = skin_path + 'Filmxymain.xml'
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
        self.scale = AVSwitch().getFramebufferScale()
        self['key_red'] = Button(_('Back'))
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        self.name = name
        self.url = url
        self.pic = pic
        self.next = info
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
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            text_clear = self.names[idx]
            if returnIMDB(text_clear):
                print('show imdb/tmdb')
        except Exception as ex:
            print(str(ex))
            print("Error: can't find Video5list in live_to_stream")

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
        i = len(self.names)
        print('iiiiii=Video5list ', i)
        if i > 0:
            idx = self['list'].getSelectionIndex()
            info = self.infos[idx]
            self['desc'].setText(info)
            self['descadd'].setText('Stream Link n°' + str(i))
        else:
            self['descadd'].setText('No Stream Link available')

    def selectionChanged(self):
        if self['list'].getCurrent():
            currentindex = self['list'].getIndex()
            print(currentindex)

    def readJsonFile(self):
        self.names = []
        self.urls = []
        self.pics = []
        self.infos = []
        content = Utils.ReadUrl(self.url)
        # if PY3:
            # content = six.ensure_str(content)
        print("content A =Video5list", content)
        try:
            # regexvideo = 'id=tab-download.*?href=(.*?)target'
            # regexvideo = 'id=tab-download.*?href=(.*?)target.*?class=movie-poster.*?data-src=(.*?)src'
            # class=movie-poster>
            # <img
            # width=250 height=350 data-src=https://www.cdnzone.org/uploads/2017/09/A-2nd-Hand-Lover-2015-cover.jpg src
            regexvideo = 'class=movie-poster.*?data-src=(.*?)src.*?id=main-down.*?href=(.*?)target'
            match = re.compile(regexvideo, re.DOTALL).findall(content)
            for pic, url in match:
            # for url, pic in match:
                picx = pic.replace(' ', '').strip()
                url = url.replace(" ", "").strip()
                print('contentglob pic ----', pic)
                print('contentglob url ----', url)
                content2 = Utils.getUrl2(url, self.url)
                print("Video5list 1 content2 =", content2)
                regexvideo2 = '<li class="signle-link"><a href="(.*?)".*?<span>(.*?)</span>.*?<strong>(.*?)</strong>'
                match2 = re.compile(regexvideo2, re.DOTALL).findall(content2)
                print("In Video5list match2 =", match2)
                for url, name1, name2 in match2:
                    name1 = name1.replace("-", "").replace(" ", "")
                    print("In Video5list vname 1 =", self.name)
                    vname = unquote(self.name)
                    print("In Video5list vname 2 =", vname)
                    name = vname + "-" + name1 + "-" + name2
                    # name = HTMLParser().unescape(name)
                    name = html_conv.html_unescape(name)
                    pic = picx
                    info = html_conv.html_unescape(self.next)
                    print('name Video5list', name)
                    print('url Video5list', url)
                    print('picx Video5list', pic)
                    print('info Video5list', info)
                    if "racaty" not in name.lower():
                        continue
                    self.names.append(name)
                    self.urls.append(url)
                    self.pics.append(pic)
                    self.infos.append(info)
                    print('sono qui -------')
            logdata("Video5list nextmodule: ", self.next)
            showlist(self.names, self['list'])
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Video5list")
        return

    def okRun(self):
        i = len(self.names)
        print('Video5list iiiiii= ', i)
        if i < 1:
            return
        try:
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            name = self.names[idx]
            url = self.urls[idx]
            info = self.infos[idx]
            pic = self.pics[idx]
            print('Video5list okrun')
            logdata("Video5list name: ", name)
            logdata("Video5list url: ", url)
            self.session.open(Playchoice, name, url, pic, info)
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Video5list")

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
            print('Video5list loadposter= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            # name = self.names[idx]
            # url = self.urls[idx]
            pixmaps = self.pics[idx]
            # # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pics[idx])
                    # print("debug pixmaps q:", pixmaps)
                    # print("debug pixmaps q:", type(pixmaps))
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as ex:
                    print(str(ex))
                    print("Error: can't find file in Video5list")
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Playchoice")
        return

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
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


class Playchoice(Screen):
    def __init__(self, session, name, url, pic, desc):
        Screen.__init__(self, session)
        self.session = session
        skin = skin_path + 'Playchoice.xml'
        with open(skin, 'r') as f:
            self.skin = f.read()
        print('self.skin: ', skin)
        f.close()
        self.setup_title = ('Select Player Stream')
        self.list = []
        self.names = []
        self.urls = []
        self.name1 = self.cleantitle(name)
        self.url = url
        self.desc = desc
        self.pic = pic
        print('In Playchoice self.pic =', pic)
        print('In Playchoice self.url =', url)
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self['list'] = rvList([])
        self['info'] = Label()
        self['info'].setText(name)
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
                                                               'rec': self.runRec,
                                                               'yellow': self.taskManager,
                                                               'instantRecord': self.runRec,
                                                               'ShortRecord': self.runRec,
                                                               'ok': self.okClicked}, -2)
        self.leftt = eTimer()
        try:
            self.leftt_conn = self.leftt.timeout.connect(self.load_poster)
        except:
            self.leftt.callback.append(self.load_poster)
        self.leftt.start(1000, True)
        self.onLayoutFinish.append(self.openTest)
        # return

    def cleantitle(self, title):
        cleanName = re.sub(r'[\<\>\:\"\/\\\|\?\*\(\)\[\]]', " ", str(title))
        cleanName = re.sub(r"  ", " ", cleanName)
        cleanName = cleanName.strip()
        return cleanName

    def taskManager(self):
        self.session.open(StreamTasks)

    def runRec(self, url):
        if 'None' not in str(url):
            self.namem3u = self.name1
            self.urlx = url
            if self.downloading is True:
                self.session.open(MessageBox, _('You are already downloading!!!'), MessageBox.TYPE_INFO, timeout=5)
                return
            else:
                if '.mp4' or '.mkv' or '.flv' or '.avi' or 'm3u8' in self.urlx:  #:
                    self.session.openWithCallback(self.download_m3u, MessageBox, _("DOWNLOAD VIDEO?\n%s" % self.namem3u), type=MessageBox.TYPE_YESNO, timeout=5, default=False)
                else:
                    self.downloading = False
                    self.session.open(MessageBox, _('Only VOD Movie allowed or not .ext Filtered!!!'), MessageBox.TYPE_INFO, timeout=5)
        else:
            self.session.open(MessageBox, _('No link available'), MessageBox.TYPE_INFO, timeout=5)

    def download_m3u(self, result):
        if result:
            # if 'm3u8' not in self.urlx:
                print('--------------not m3u8-----------------')
                path = urlparse(self.urlx).path
                ext = '.mp4'
                ext = splitext(path)[1]
                if ext != '.mp4' or ext != '.mkv' or ext != '.avi' or ext != '.flv':  # or ext != 'm3u8':
                    ext = '.mp4'
                fileTitle = re.sub(r'[\<\>\:\"\/\\\|\?\*\[\]]', '_', self.namem3u)
                fileTitle = re.sub(r' ', '_', fileTitle)
                fileTitle = re.sub(r'_+', '_', fileTitle)
                fileTitle = fileTitle.replace("(", "_").replace(")", "_").replace("#", "").replace("+", "_").replace("\'", "_").replace("'", "_")
                fileTitle = fileTitle.replace(":", "").replace("[", "").replace("]", "").replace("!", "_").replace("&", "_")
                fileTitle = fileTitle.lower() + ext
                self.in_tmp = Path_Movies + fileTitle
                # self.urlx = self.urlx.strip()
                # if PY3:
                    # self.urlx = self.urlx.encode()
                print('path download = ', self.in_tmp)
                try:
                    import subprocess
                    useragent = "--header='User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'"
                    WGET = '/usr/bin/wget'
                    if "https" in str(self.urlx):
                        WGET = '/usr/bin/wget --no-check-certificate'
                    cmd = WGET + " %s -c '%s' -O '%s'" % (useragent, self.urlx, self.in_tmp)
                    myCmd = "%s" % str(cmd)
                    subprocess.Popen(myCmd, shell=True, executable='/bin/bash')
                    self['info'].setText(_('Download in progress... %s' % fileTitle))
                    self.downloading = True
                    pmovies = True
                    print('self url is : ', self.urlx)
                    print('url type: ', type(self.urlx))

                    # self.LastJobView()
                    # # test another ufff   --->>   urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1129)
                    # url = urlopen(self.urlx.decode('ASCII')) #.read()
                    # f = open(self.in_tmp, 'wb')
                    # f.close()
                    # job = downloadJob(url, self.in_tmp, fileTitle)
                    # job.afterEvent = "close"
                    # job_manager.AddJob(job)
                    # job_manager.failed_jobs = []
                    # self.session.openWithCallback(self.ImageDownloadCB, JobView, job, backgroundable=False, afterEventChangeable=False)

                except URLError as e:
                    print("Download failed !!\n%s" % e)
                    self.session.openWithCallback(self.ImageDownloadCB, MessageBox, _("Download Failed !!") + "\n%s" % e, type=MessageBox.TYPE_ERROR)
                    self.downloading = False
                    pmovies = False
            # else:
                # self['info'].setText(_('Download failed!') + self.dom + _('... Not supported'))

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
            urlxy = url
        else:
            if "mediashore" in name.lower():
                from .resolver.fembed import FEmbedResolver
                res = FEmbedResolver()
                urlxy = res.get_media_url(urlx)
            elif "racaty" in name.lower():
                from .resolver.racaty import RacatyResolver
                res = RacatyResolver()
                urlxy = res.get_media_url(urlx)
            elif "sbfast" in name.lower():
                from .resolver.streamsb import StreamSBResolver
                res = StreamSBResolver()
                urlxy = res.get_media_url(urlx)
        # self.urlxy = urlxy
        return urlxy

    def okClicked(self):
        i = len(self.names)
        print('Video5list iiiiii= ', i)
        if i < 1:
            return
        try:
            idx = self['list'].getSelectionIndex()
            name = self.name1
            name = name.replace("%28%", "(").replace("%29%", ")")
            url = self.url
            if idx == 0:
                # from Tools.BoundFunction import boundFunction
                # self.racat = eTimer()
                # try:
                    # self.racat_conn = self.racat.timeout.connect(self.racatyx(name, url))
                # except:
                    # self.racat.callback.append(self.racatyx(name, url))
                url = self.racatyx(name, url)
                # self.racat.start(2500, True)
                # url = self.urlxy
                print('In playVideo url D=', url)
                self.play(name, url)
            elif idx == 1:
                url = self.url
                print('In playVideo runRec url D=', url)
                self.racat = eTimer()
                self.urlx = self.racatyx(name, url)
                self.racat.start(2500, True)
                self.runRec(self.urlx)
            elif idx == 2:
                self.name = self.name1
                url = self.url
                print('In playVideo url B=', url)
                try:
                    os.remove('/tmp/hls.avi')
                except:
                    pass
                header = ''
                cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/filmxy/resolver/hlsclient.py" "' + url + '" "1" "' + header + '" + &'
                print('In playVideo cmd =', cmd)
                os.system(cmd)
                os.system('sleep 3')
                url = '/tmp/hls.avi'
                self.play(self.name, url)
            elif idx == 3:
                url = self.url
                print('In playVideo url A=', url)
                try:
                    os.remove('/tmp/hls.avi')
                except:
                    pass
                cmd = 'python "/usr/lib/enigma2/python/Plugins/Extensions/filmxy/resolver/tsclient.py" "' + url + '" "1" + &'
                print('hls cmd = ', cmd)
                os.system(cmd)
                os.system('sleep 3')
                url = '/tmp/hls.avi'
                self.name = self.name1
                self.play(self.name, url)
            else:
                if idx == 4:
                    self.name = self.name1
                    url = self.url
                    print('In playVideo url D=', url)
                    self.play2(self.name, url)
            return
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Playchoice")

    def playfile(self, serverint):
        if 'None' not in str(self.url):
            self.serverList[serverint].play(self.session, self.url, self.name)
        else:
            self.session.open(MessageBox, _('No link available'), MessageBox.TYPE_INFO, timeout=5)
        self.close()

    def play(self, name, url):
        desc = self.desc
        # self.url = url
        # name = self.name1
        logdata("Playstream2 name: ", name)
        logdata("Playstream2 url: ", url)
        if 'None' not in str(url):
            self.session.open(Playstream2, name, url, desc)
        else:
            self.session.open(MessageBox, _('No link available'), MessageBox.TYPE_INFO, timeout=5)
        self.close()

    def play2(self, name, url):
        if Utils.isStreamlinkAvailable():
            desc = self.desc
            name = self.name
            # if os.path.exists("/usr/sbin/streamlinksrv"):
            # url = self.url
            url = url.replace(':', '%3a')
            print('In filmxy url =', url)
            if 'None' not in str(url):
                ref = '5002:0:1:0:0:0:0:0:0:0:' + 'http%3a//127.0.0.1%3a8088/' + str(url)
                sref = eServiceReference(ref)
                print('SREF: ', sref)
                sref.setName(name)
                self.session.open(Playstream2, name, sref, desc)
            else:
                self.session.open(MessageBox, _('No link available'), MessageBox.TYPE_INFO, timeout=5)
        else:
            self.session.open(MessageBox, _('Install Streamlink first'), MessageBox.TYPE_INFO, timeout=5)

    def cancel(self):
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)
        self.close()

    def load_poster(self):
        try:
            i = len(self.names)
            print('iiiiii= ', i)
            if i < 1:
                return
            idx = self['list'].getSelectionIndex()
            print('idx: ', idx)
            pixmaps = self.pic
            print('pixmap  : ', pixmaps)
            if str(res_plugin_path) in pixmaps:
                self.downloadPic(None, pixmaps)
                return
            # pixmaps = six.ensure_binary(self.pics[idx])
            if pixmaps != "" or pixmaps != "n/A" or pixmaps is not None or pixmaps != "null":
                try:
                    if PY3:
                        pixmaps = six.ensure_binary(self.pic)
                    # print("debug pixmaps t:", pixmaps)
                    # print("debug pixmaps t:", type(pixmaps))
                    if pixmaps.startswith(b"https") and sslverify:
                        parsed_uri = urlparse(pixmaps)
                        domain = parsed_uri.hostname
                        sniFactory = SNIFactory(domain)
                        # if six.PY3:
                            # pixmaps = pixmaps.encode()
                        downloadPage(pixmaps, pictmp, sniFactory, timeout=5).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                    else:
                        downloadPage(pixmaps, pictmp).addCallback(self.downloadPic, pictmp).addErrback(self.downloadError)
                except Exception as ex:
                    print(str(ex))
                    print("Error: can't find file or read data live_to_stream")
            return
        except Exception as ex:
            print(str(ex))
            print("Error: can't find file or read data in Playchoice")

    def downloadPic(self, data, pictmp):
        if os.path.exists(pictmp):
            try:
                self.poster_resize(pictmp)
            except Exception as ex:
                print("* error ** %s" % ex)
                pass

    def downloadError(self, png):
        try:
            if fileExists(png):
                self.poster_resize(png)
        except Exception as ex:
            self.poster_resize(no_cover)
            print(str(ex))
            print('exe downloadError')

    def poster_resize(self, png):
        self["poster"].hide()
        size = self['poster'].instance.size()
        self.picload = ePicLoad()
        self.scale = AVSwitch().getFramebufferScale()
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


class Playstream2(Screen, InfoBarMenu, InfoBarBase, InfoBarSeek, InfoBarNotifications, InfoBarAudioSelection, TvInfoBarShowHide, InfoBarSubtitleSupport):
    STATE_IDLE = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    ENABLE_RESUME_SUPPORT = True
    ALLOW_SUSPEND = True
    # screen_timeout = 4000

    def __init__(self, session, name, url, desc):
        global streaml
        Screen.__init__(self, session)
        self.session = session
        global _session
        _session = session
        self.skinName = 'MoviePlayer'
        streaml = False
        InfoBarMenu.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarBase.__init__(self, steal_current_service=True)
        TvInfoBarShowHide.__init__(self)
        InfoBarSubtitleSupport.__init__(self)
        InfoBarAudioSelection.__init__(self)
        InfoBarSeek.__init__(self, actionmap='InfobarSeekActions')
        try:
            self.init_aspect = int(self.getAspect())
        except:
            self.init_aspect = 0
        self.new_aspect = self.init_aspect
        self.srefInit = self.session.nav.getCurrentlyPlayingServiceReference()
        self.service = None
        self.name = html_conv.html_unescape(name)
        self.icount = 0
        url = url.replace(':', '%3a')
        self.url = url
        self.desc = desc
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
                                     'InfobarSeekActions'], {'leavePlayer': self.cancel,
                                                             'epg': self.showIMDB,
                                                             'info': self.showIMDB,
                                                             'tv': self.cicleStreamType,
                                                             'stop': self.leavePlayer,
                                                             'red': self.cicleStreamType,
                                                             'cancel': self.cancel,
                                                             'back': self.cancel}, -1)
        if '8088' in str(self.url):
            self.onFirstExecBegin.append(self.slinkPlay)
        else:
            self.onFirstExecBegin.append(self.cicleStreamType)
        self.onClose.append(self.cancel)

    def getAspect(self):
        return AVSwitch().getAspectRatioSetting()

    def getAspectString(self, aspectnum):
        return {0: _('4:3 Letterbox'),
                1: _('4:3 PanScan'),
                2: _('16:9'),
                3: _('16:9 always'),
                4: _('16:10 Letterbox'),
                5: _('16:10 PanScan'),
                6: _('16:9 Letterbox')}[aspectnum]

    def setAspect(self, aspect):
        map = {0: '4_3_letterbox',
               1: '4_3_panscan',
               2: '16_9',
               3: '16_9_always',
               4: '16_10_letterbox',
               5: '16_10_panscan',
               6: '16_9_letterbox'}
        config.av.aspectratio.setValue(map[aspect])
        try:
            AVSwitch().setAspectRatio(aspect)
        except:
            pass

    def av(self):
        temp = int(self.getAspect())
        temp = temp + 1
        if temp > 6:
            temp = 0
        self.new_aspect = temp
        self.setAspect(temp)

    def showIMDB(self):
        try:
            text_clear = self.name
            if returnIMDB(text_clear):
                print('show imdb/tmdb')
        except Exception as ex:
            print(str(ex))
            print("Error: can't find Playstream2 in live_to_stream")

    def slinkPlay(self, url):
        name = self.name
        ref = "{0}:{1}".format(url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def openPlay(self, servicetype, url):
        name = self.name
        ref = "{0}:0:0:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
        print('reference:   ', ref)
        if streaml is True:
            url = 'http://127.0.0.1:8088/' + str(url)
            ref = "{0}:0:1:0:0:0:0:0:0:0:{1}:{2}".format(servicetype, url.replace(":", "%3a"), name.replace(":", "%3a"))
            print('streaml reference:   ', ref)
        print('final reference:   ', ref)
        sref = eServiceReference(ref)
        sref.setName(name)
        self.session.nav.stopService()
        self.session.nav.playService(sref)

    def cicleStreamType(self):
        global streml
        streaml = False
        # from itertools import cycle, islice
        # self.servicetype = '4097'
        self.servicetype = str(config.plugins.filmxy.services.value)
        print('servicetype1: ', self.servicetype)
        url = str(self.url)
        if str(splitext(url)[-1]) == ".m3u8":
            if self.servicetype == "1":
                self.servicetype = "4097"
        # currentindex = 0
        # streamtypelist = ["4097"]
        # # if "youtube" in str(url):
            # # self.mbox = self.session.open(MessageBox, _('For Stream Youtube coming soon!'), MessageBox.TYPE_INFO, timeout=5)
            # # return
        # if Utils.isStreamlinkAvailable():
            # streamtypelist.append("5002") #ref = '5002:0:1:0:0:0:0:0:0:0:http%3a//127.0.0.1%3a8088/' + url
            # streaml = True
        # if os.path.exists("/usr/bin/gstplayer"):
            # streamtypelist.append("5001")
        # if os.path.exists("/usr/bin/exteplayer3"):
            # streamtypelist.append("5002")
        # if os.path.exists("/usr/bin/apt-get"):
            # streamtypelist.append("8193")
        # for index, item in enumerate(streamtypelist, start=0):
            # if str(item) == str(self.servicetype):
                # currentindex = index
                # break
        # nextStreamType = islice(cycle(streamtypelist), currentindex + 1, None)
        # self.servicetype = str(next(nextStreamType))
        print('servicetype2: ', self.servicetype)
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
        if os.path.isfile('/tmp/hls.avi'):
            os.remove('/tmp/hls.avi')
        self.session.nav.stopService()
        self.session.nav.playService(self.srefInit)
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
        skin = skin_path + 'myconfig.xml'
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

    def setInfo(self):
        entry = str(self.getCurrentEntry())
        if entry == _('Set the path to the Cache folder'):
            self['description'].setText(_("Press Ok to select the folder containing the picons files"))
        if entry == _('Set the path Movie folder'):
            self['description'].setText(_("Folder Movie Path (eg.: /media/hdd/movie), Press OK - Enigma restart required"))
        if entry == _('Services Player Reference type'):
            self['description'].setText(_("Configure Service Player Reference"))
        return

    def paypal2(self):
        conthelp = "If you like what I do you\n"
        conthelp += " can contribute with a coffee\n\n"
        conthelp += "scan the qr code and donate € 1.00"
        return conthelp

    def layoutFinished(self):
        paypal = self.paypal2()
        self["paypal"].setText(paypal)
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
        self["config"].list = self.list
        self["config"].l.setList(self.list)
        # self.setInfo()

    def cachedel(self):
        fold = config.plugins.filmxy.cachefold.value + "/pic"
        cmd = "rm " + fold + "/*"
        os.system(cmd)
        self.mbox = self.session.open(MessageBox, _('All cache fold are empty!'), MessageBox.TYPE_INFO, timeout=5)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        print("current selection:", self["config"].l.getCurrentSelection())
        self.createSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        print("current selection:", self["config"].l.getCurrentSelection())
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
            print('openDirectoryBrowser get failed: ', str(e))

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
        skin = skin_path + "/StreamTasks.xml"
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
        file1 = False
        filelist = ''
        self.pth = ''
        if os.path.isdir(Path_Movies):
            filelist = os.listdir(Path_Movies)
        path = Path_Movies

        if filelist is not None:
            file1 = True
            filelist.sort()
            for filename in filelist:
                if os.path.isfile(path + filename):
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
        desc = 'local'
        pic = ''
        if current:
            if current[0] == "movie":
                if file1 is True:
                    path = Path_Movies
                url = path + current[1]
                name = current[1]
                file1 = False
                isFile = os.path.isfile(url)
                if isFile:
                    self.session.open(Playstream2, name, url, desc)
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
        sel2 = self.pth + current[1]
        dom = sel
        # dom2 = sel2
        self.session.openWithCallback(self.callMyMsg1, MessageBox, _("Do you want to remove %s ?") % dom, MessageBox.TYPE_YESNO, timeout=15, default=False)

    def callMyMsg1(self, result):
        if result:
            current = self["movielist"].getCurrent()
            sel = Path_Movies + current[1]
            # sel2 = self.pth + current[1]
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


# class downloadJob(Job):
    # def __init__(self, toolbox, cmdline, filename, filmtitle):
        # print("**** downloadJob init ***")
        # # Job.__init__(self, 'Download:' + ' %s' % filmtitle)
        # Job.__init__(self, filmtitle)
        # self.filename = filename
        # self.toolbox = toolbox
        # self.retrycount = 0
        # # downloadTask(self, cmdline, filename)
        # downloadTask(self, cmdline, filename, filmtitle)

    # def retry(self):
        # self.retrycount += 1
        # self.restart()

    # def cancel(self):
        # self.abort()
        # os.system("rm -f %s" % self.filename)

    # def createMetaFile(self, filename, filmtitle):
        # try:
            # serviceref = eServiceReference(4097, 0, filename)
            # with open("%s.meta" % (filename), "w") as f:
                # f.write("%s\n%s\n%s\n%i\n" % (serviceref.toString(), filmtitle, "", time.time()))
        # except Exception as e:
            # print(e)
        # return

    # def download_finished(self, filename, filmtitle):
        # self.createMetaFile(filename, filmtitle)


# class DownloaderPostcondition(Condition):
    # RECOVERABLE = True

    # def check(self, task):
        # if task.returncode == 0 or task.error is None:
            # return True
        # else:
            # return False
            # return

    # def getErrorMessage(self, task):
        # return {
            # task.ERROR_CORRUPT_FILE: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("DOWNLOADED FILE CORRUPTED:") + '\n%s' % task.error_message,
            # task.ERROR_RTMP_ReadPacket: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("COULD NOT READ RTMP PACKET:") + '\n%s' % task.error_message,
            # task.ERROR_SEGFAULT: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("SEGMENTATION FAULT:") + '\n%s' % task.error_message,
            # task.ERROR_SERVER: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("SERVER RETURNED ERROR:") + '\n%s' % task.error_message,
            # task.ERROR_UNKNOWN: _("MOVIE DOWNLOAD FAILED!") + '\n\n' + _("UNKNOWN ERROR:") + '\n%s' % task.error_message
        # }[task.error]


# class downloadTask(Task):
    # # def __init__(self, job, cmdline, filename):
    # def __init__(self, job, cmdline, filename, filmtitle):
        # Task.__init__(self, job, filmtitle)
        # self.postconditions.append(DownloaderPostcondition())
        # self.job = job
        # self.toolbox = job.toolbox
        # self.url = cmdline
        # self.filename = filename
        # self.filmtitle = filmtitle
        # self.error_message = ""
        # self.last_recvbytes = 0
        # self.error_message = None
        # self.download = None
        # self.aborted = False

    # def run(self, callback):
        # from .Downloader import DownloadWithProgress
        # self.callback = callback
        # self.download = DownloadWithProgress(self.url, self.filename)
        # self.download.addProgress(self.download_progress)
        # # self.download.start().addEnd(self.download_finished).addError(self.download_failed)
        # self.download.start().addCallback(self.afterRun).addErrback(self.download_failed)
        # print("[downloadTask] downloading", self.url, "to", self.filename)

    # def abort(self):
        # self.downloading = False
        # print("[downloadTask] aborting", self.url)
        # if self.download:
            # self.download.stop()
        # self.aborted = True

    # def download_progress(self, recvbytes, totalbytes):
        # if (recvbytes - self.last_recvbytes) > 10000:  # anti-flicker
            # self.progress = int(100 * (float(recvbytes) // float(totalbytes)))
            # self.name = _("Downloading") + ' ' + _("%d of %d kBytes") % (recvbytes // 1024, totalbytes // 1024)
            # # self.blockSize = max(min(self.totalSize // 100, 1024), 131071) if self.totalSize else 65536
            # self.last_recvbytes = recvbytes

    # def download_failed(self, failure_instance=None, error_message=""):
        # self.downloading = False
        # self.error_message = error_message
        # if error_message == "" and failure_instance is not None:
            # self.error_message = failure_instance.getErrorMessage()
        # Task.processFinished(self, 1)

    # def download_finished(self, string=""):
        # self.downloading = False
        # if self.aborted:
            # self.finish(aborted=True)
        # else:
            # Task.processFinished(self, 0)

    # def afterRun(self):
        # if self.getProgress() == 0:
            # try:
                # self.toolbox.download_failed()
            # except:
                # pass
        # elif self.getProgress() == 100:
            # try:
                # self.toolbox.download_finished()
                # self.downloading = False
                # message = "Movie successfully transfered to your HDD!" + "\n" + self.filename
                # Utils.web_info(message)
            # except:
                # pass
        # pass


class AutoStartTimerFxy:

    def __init__(self, session):
        self.session = session
        global _firstStart
        print("*** running AutoStartTimerFxy ***")
        if _firstStart:
            self.runUpdate()

    def runUpdate(self):
        print("*** running update ***")
        try:
            from . import Update
            Update.upd_done()
            _firstStart = False
        except Exception as e:
            print('error Fxy', str(e))


def autostart(reason, session=None, **kwargs):
    print("*** running autostart ***")
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
