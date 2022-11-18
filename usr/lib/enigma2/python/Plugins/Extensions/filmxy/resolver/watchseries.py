# -*- coding: UTF-8 -*-

# import xbmc
# import xbmcplugin
# import xbmcgui
# import adnutils
# from adnutils import *
from . import Utils
import re


def sources(name, season, episode):
    print("In watchseries.py name =", name)
    print("In watchseries.py season =", season)
    print("In watchseries.py episode =", episode)
    # url = "https://watchseriess.net/series/game-of-thrones-season-8-episode-5"
    name = name.lower()
    name = name.replace("+", "-")
    url = "https://watchseriess.net/series/" + name + "-season-" + season + "-episode-" + episode
    print("In watchseries.py url =", url)
    content = Utils.getUrl(url)
    # print("In watchseries.py content =", content)
    regexvideo = 'data-video="(.*?)\?.*?server.*?>(.*?)<'
    match = re.compile(regexvideo, re.DOTALL).findall(content)
    print("In watchseries match =", match)
    return match
