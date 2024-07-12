#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import traceback
import requests
import re
from .resolver import cfscrape
# from tqdm import tqdm
from random import choice

# Disable TLS Warnings
import urllib3
urllib3.disable_warnings()

FF_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'
OPERA_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36 OPR/67.0.3575.97'
EDGE_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363'
CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4136.7 Safari/537.36'
SAFARI_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15'

# Random user agent
_USER_AGENTS = [FF_USER_AGENT, OPERA_USER_AGENT, EDGE_USER_AGENT, CHROME_USER_AGENT, SAFARI_USER_AGENT]
RAND_UA = choice(_USER_AGENTS)
# ██████╗  █████╗  ██████╗ █████╗ ████████╗██╗   ██╗     ██████╗ ██╗     
# ██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝╚██╗ ██╔╝     ██╔══██╗██║     
# ██████╔╝███████║██║     ███████║   ██║    ╚████╔╝█████╗██║  ██║██║     
# ██╔══██╗██╔══██║██║     ██╔══██║   ██║     ╚██╔╝ ╚════╝██║  ██║██║     
# ██║  ██║██║  ██║╚██████╗██║  ██║   ██║      ██║        ██████╔╝███████╗
# ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝      ╚═╝        ╚═════╝ ╚══════╝

def read_txt(abs):
    with open(abs) as f:
        return [u.strip() for u in f.readlines()]


def parse_prefs():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-u', '--urls',
        nargs='+', required=True,
        help='URLs separated by a space or an abs path to a txt file.'
    )
    parser.add_argument(
        '-o', '--output-path',
        default='Racaty_downloads',
        help='Abs output directory.'
    )
    parser.add_argument(
        '-ov', '--overwrite',
        action='store_true',
        help='Overwrite file if already exists.'
    )
    args = parser.parse_args()
    if args.urls[0].endswith('.txt'):
        args.urls = read_txt(args.urls[0])
    return args


def dir_setup():
    if not os.path.isdir(cfg.output_path):
        os.makedirs(cfg.output_path)


def err(txt):
    print(txt)
    traceback.print_exc()


def extract(url):
    ses = requests.Session()
    ses.headers = {
        'referer': 'https://racaty.io',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
        'accept': 'application/json'
    }
    regex = r'https://racaty.io/([a-zA-Z\d]{12})'
    match = re.match(regex, url)
    _id = match.group(1)

    payload='op=download2&id=' + str(_id) +'&rand=&referer=&method_free=&method_premium='

    scraper = cfscrape.create_scraper()
    response = scraper.post(url, data=payload).text

    content = re.search(r'id="uniqueExpirylink"\s*href="([^"]+)', response, re.DOTALL)
    file_url = content.group(1).replace(' ', '%20')
    file_name = re.search(r'//.*/.*/(.*)', file_url)
    fname = file_name.group(1)
    return file_url, fname


def get_file(ref, url):
    s.headers.update({
        'Range': "bytes=0-",
        'Referer': ref
    })
    r = s.get(url, stream=True, verify=False)
    del s.headers['Range']
    del s.headers['Referer']
    r.raise_for_status()
    length = int(r.headers['Content-Length'])
    return r, length


# def download(ref, url, fname):
    # print(fname)
    # abs = os.path.join(cfg.output_path, fname)
    # if os.path.isfile(abs):
        # if cfg.overwrite:
            # print("File already exists locally. Will overwrite.")
        # else:
            # print("File already exists locally.")
            # return
    # r, size = get_file(ref, url)
    # with open(abs, 'wb') as f:
        # with tqdm(total=size, unit='B', unit_scale=True, unit_divisor=1024, initial=0, miniters=1) as bar:
            # for chunk in r.iter_content(32*1024):
                # if chunk:
                    # f.write(chunk)
                    # bar.update(len(chunk))


def main(url):
    file_url, fname = extract(url)
    # download(url, file_url, fname)


if __name__ == '__main__':
    try:
        if hasattr(sys, 'frozen'):
            os.chdir(os.path.dirname(sys.executable))
        else:
            os.chdir(os.path.dirname(__file__))
    except OSError:
        pass

    s = requests.Session()
    s.headers.update({
        'User-Agent': RAND_UA
    })

    print("""
██████╗  █████╗  ██████╗ █████╗ ████████╗██╗   ██╗     ██████╗ ██╗
██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝╚██╗ ██╔╝     ██╔══██╗██║
██████╔╝███████║██║     ███████║   ██║    ╚████╔╝█████╗██║  ██║██║
██╔══██╗██╔══██║██║     ██╔══██║   ██║     ╚██╔╝ ╚════╝██║  ██║██║
██║  ██║██║  ██║╚██████╗██║  ██║   ██║      ██║        ██████╔╝███████╗
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝      ╚═╝        ╚═════╝ ╚══════╝
    """)
    cfg = parse_prefs()
    dir_setup()
    total = len(cfg.urls)
    for num, url in enumerate(cfg.urls, 1):
        print("{} of {}:".format(num, total))
        try:
            main(url)
        except Exception as e:
            err('URL failed.')
