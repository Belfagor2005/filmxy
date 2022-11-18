
import urllib2
"""
from Tools.BoundFunction import boundFunction

from Components.Sources.List import List
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmap, MultiContentEntryPixmapAlphaTest
from urllib2 import urlopen
from Components.MenuList import MenuList
from Components.Label import Label

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import NumberActionMap
from Components.Input import Input
from Components.Pixmap import Pixmap
from Components.FileList import FileList
from Screens.ChoiceBox import ChoiceBox
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Screens.InputBox import InputBox, PinInput

from twisted.web.client import getPage, downloadPage
#from Plugins.Extensions.VlcPlayer.VlcServerConfig import vlcServerConfig

from enigma import eServiceReference
from enigma import eServiceCenter
from Screens.InfoBar import MoviePlayer
import os
import re

#from Skins import *
#from Utils import Getvid, downloadJob, Playvid, PlayPlaylist, RSList, RSListEntry, showlist, Getvlc

from Components.Task import Task, Job, job_manager as JobManager, Condition
#from TaskView2 import JobView2 as JobView
from Components.Button import Button

from Components.config import config, ConfigEnableDisable, ConfigSubsection, \
			 ConfigYesNo, ConfigClock, getConfigListEntry, \
			 ConfigSelection, ConfigNumber, ConfigText
from Components.ConfigList import ConfigListScreen
import xpath
from Plugins.Extensions.KodiDirect.lib.Utils import *
"""
def getUrl(url):
        print "Here in getUrl url =", url
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	return link
	
def getUrl2(url, referer):
        print "Here in getUrl url =", url
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        req.add_header('Referer', referer)
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	return link	

class PlayVideo(Screen):

    def __init__(self, session, names, urls):
		
                Screen.__init__(self, session)
                self.skinName = "KodiMenusScreen"
		title = "Videos list"
		self["title"] = Button(title)
#		self.setTitle(title)
		self.list = []
#        	self["list"] = MenuList([])
#		self["info"] = Label()
		self["menu"] = List(self.list)
                self["menu"] = RSList([])
		self["info"] = Label()
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button(_("Select"))
		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "TimerEditActions"],
		{
			"red": self.cancel,
			"green": self.okClicked,
			"ok": self.okClicked,
			"cancel": self.cancel,
		}, -2)
		
		
                self["bild"] = Label()
                self["pixmap"] = Pixmap()
		
                self.names = names
                self.urls = urls
#                ######print " self.url =", self.url
                self.srefOld = self.session.nav.getCurrentlyPlayingServiceReference()
                self.onLayoutFinish.append(self.openTest)

    def cancel(self):
                self.session.nav.playService(self.srefOld)
                self.close()
    def openTest(self):
                showlist(self.names, self["menu"])
    def okClicked(self):
            ientry = self["menu"].getSelectionIndex()
            if ientry is not None:
                url = self.urls[ientry]
                name = self.names[ientry]
                print "In okClicked name =", name
                print "In okClicked url =", url
                vidurl = self.getVidurl(name, url)
                desc = " "
                if vidurl is not None:
                    if "http" in vidurl:
                       self.session.open(Playvid, name, vidurl, desc)
            else:
                return

    def getVidurl(self, name, url):
          print "In getVidurl url =", url
          print "In getVidurl name =", name
          if ("nowvideo" in name) or ("nowvideo" in url):
                   print "In getVidurl nowvideo url 2=", url
                   from resolvers.nowvideo import resolve
          elif ("allvid" in name) or ("allvid" in url):               
                   from resolvers.allvid import resolve
          elif ("exashare" in name) or ("exashare" in url):                
                   from resolvers.exashare import resolve         
          elif ("streamin" in name) or ("streamin" in url): 
                   from resolvers.streamin import resolve
          elif ("vidzi" in name) or ("vidzi" in url): 
                   from resolvers.vidzi import resolve
          elif ("nosvideo" in name) or ("nosvideo" in url): 
                   from resolvers.nosvideo import resolve
          elif ("openload" in name) or ("openload" in url): 
                   from resolvers.openload import resolve         
          elif ("uptobox" in name) or ("uptobox" in url): 
                   from resolvers.uptobox import resolve
          elif ("filepup" in name) or ("filepup" in url): 
                   from resolvers.filepup2 import resolve
          elif ("vidbull" in name) or ("vidbull" in url): 
                   from resolvers.vidbull import resolve
          elif ("vodlocker" in name) or ("vodlocker" in url): 
                   print "In getVidurl vodlockero url 2=", url
                   from resolvers.vodlocker import resolve
          elif ("vidto" in name) or ("vidto" in url): 
                   print "In getVidurl vidto url 2=", url
                   from resolvers.vidto import resolve
          elif ("videomega" in name) or ("videomega" in url): 
                   print "In getVidurl videomega url =", url
                   from resolvers.videomega import resolve
          elif ("youwatch" in name) or ("youwatch" in url): 
                   from resolvers.youwatch import resolve   
          elif ("zstream" in name) or ("zstream" in url): 
                   from resolvers.zstream import resolve            
          try:               
                   vidurl = resolve(url)
                   print "In getVidurl vidurl =", vidurl
                   return vidurl
          except:         
                   print "In getVidurl url B=", url
                   return url
















