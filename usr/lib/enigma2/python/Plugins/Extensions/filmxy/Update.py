#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
PY3 = sys.version_info.major >= 3
print("Update.py")


def upd_done():
    from os import popen
    cmd01 = "wget http://patbuweb.com/filmxy/filmxy.tar -O /tmp/filmxy.tar ; tar -xvf /tmp/filmxy.tar -C /"
    cmd02 = "wget --no-check-certificate -U 'Enigma2 - filmxy Plugin' -c 'http://patbuweb.com/filmxy/filmxy.tar' -O '/tmp/filmxy.tar'; tar -xvf /tmp/filmxy.tar -C /"
    cmd22 = 'find /usr/bin -name "wget"'
    res = popen(cmd22).read()
    if 'wget' not in res.lower():
        cmd23 = 'apt-get update && apt-get install wget'
        popen(cmd23)
    try:
        popen(cmd02)
    except:
        popen(cmd01)
    return

'''

import sys
from twisted.web.client import downloadPage
PY3 = sys.version_info.major >= 3
print("Update.py")


def upd_done():
    print("In upd_done")
    xfile = 'http://patbuweb.com/filmxy/filmxy.tar'
    if PY3:
        xfile = b"http://patbuweb.com/filmxy/filmxy.tar"
        print("Update.py in PY3")
    import requests
    response = requests.head(xfile)
    if response.status_code == 200:
        # print(response.headers['content-length'])
        fdest = "/tmp/filmxy.tar"
        print("Code 200 upd_done xfile =", xfile)
        downloadPage(xfile, fdest).addCallback(upd_last)
    elif response.status_code == 404:
        print("Error 404")
    else:
        return


def upd_last(fplug):
    import time
    import os
    time.sleep(5)
    fdest = "/tmp/filmxy.tar"
    if os.path.isfile(fdest) and os.stat(fdest).st_size > 10000:
        cmd = "tar -xvf /tmp/filmxy.tar -C /"
        print("cmd A =", cmd)
        os.system(cmd)
        os.remove('/tmp/filmxy.tar')
    return
'''