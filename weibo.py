#!/usr/bin/env python
# _*_ coding=utf8 _*_
import re
import json
import urllib
import base64
import os
import binascii
import sys
import rsa
import requests
import threading

import logging
from weibo_conf import UID,THREAD
#logging.basicConfig(level=logging.DEBUG)


WBCLIENT = 'ssologin.js(v1.4.5)'
user_agent = (
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.11 (KHTML, like Gecko) '
    'Chrome/20.0.1132.57 Safari/536.11'
)
session = requests.session()
session.headers['User-Agent'] = user_agent
ALBUM_ID = -1


def encrypt_passwd(passwd, pubkey, servertime, nonce):
    key = rsa.PublicKey(int(pubkey, 16), int('10001', 16))
    message = str(servertime) + '\t' + str(nonce) + '\n' + str(passwd)
    passwd = rsa.encrypt(message, key)
    return binascii.b2a_hex(passwd)


def wblogin(username, password):
    resp = session.get(
        'http://login.sina.com.cn/sso/prelogin.php?'
        'entry=sso&callback=sinaSSOController.preloginCallBack&'
        'su=%s&rsakt=mod&client=%s' %
        (base64.b64encode(username), WBCLIENT)
    )

    pre_login_str = re.match(r'[^{]+({.+?})', resp.content).group(1)
    pre_login = json.loads(pre_login_str)

 #   pre_login = json.loads(pre_login_str)
    data = {
        'entry': 'weibo',
        'gateway': 1,
        'from': '',
        'savestate': 7,
        'userticket': 1,
        'ssosimplelogin': 1,
        'su': base64.b64encode(urllib.quote(username)),
        'service': 'miniblog',
        'servertime': pre_login['servertime'],
        'nonce': pre_login['nonce'],
        'vsnf': 1,
        'vsnval': '',
        'pwencode': 'rsa2',
        'sp': encrypt_passwd(password, pre_login['pubkey'],
                             pre_login['servertime'], pre_login['nonce']),
        'rsakv' : pre_login['rsakv'],
        'encoding': 'UTF-8',
        'prelt': '115',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.si'
               'naSSOController.feedBackUrlCallBack',
        'returntype': 'META'
    }
    resp = session.post(
        'http://login.sina.com.cn/sso/login.php?client=%s' % WBCLIENT,
        data=data
    )

    login_url = re.search(r'replace\([\"\']([^\'\"]+)[\"\']',
                          resp.content).group(1)
    resp = session.get(login_url)
    login_str = re.match(r'[^{]+({.+?}})', resp.content).group(1)
    #return json.loads(login_str)
    get_album_id(UID)
    picname_list= []
    page = 1
    while True:
        des_url = 'http://photo.weibo.com/photos/get_all?uid=%s&album_id=%s&count=30&page=%s&type=3' % (UID,ALBUM_ID,page)
        resp = session.get(des_url)
        rep_data = resp.json()['data']['photo_list']
        if len(rep_data) == 0:
            break
        for each in rep_data:
            try:
                if each['pic_name'] not in picname_list:
                    picname_list.append(each['pic_name'])
            except:
                pass
        page += 1
    sort_dir = str(UID)
    if os.path.exists('./' + sort_dir):
        os.system('rm -rf ./%s' % sort_dir)
    os.mkdir('./' + sort_dir)    
    picname_list = div_list(picname_list,THREAD)    
    print len(picname_list)
    thread = []
    for i in range(THREAD):
        thread.append(dojob(download,picname_list,sort_dir,i))
    for each in thread:
        each.start()
    for each in thread:
        each.join()

    print 'All download job done.'


class dojob(threading.Thread):
    def __init__(self,func,picname_list,sort_dir,index):
        threading.Thread.__init__(self)
        self.func = func
        self.picname_list = picname_list
        self.sort_dir = sort_dir
        self.index = index

    def run(self):
        self.func(self.picname_list,self.sort_dir,self.index)

def div_list(picname_list,THREAD):
    size = len(picname_list) / int(THREAD) + 1
    l = [picname_list[i:i+int(size)] for i in range(0,len(picname_list),size)]
    return l

def download(picname_list,sort_dir,index):
    i = 0
    for picname in picname_list[index]:
        download_url = 'http://ww3.sinaimg.cn/large/%s.jpg' % picname
        urllib.urlretrieve(download_url, './' + sort_dir + '/' + picname + '.jpg')
        print 'Download ' + picname + ' successed.'


def get_album_id(UID):
    global ALBUM_ID
    url = 'http://photo.weibo.com/albums/get_all?uid=%s&page=1&count=20' % UID
    rep = session.get(url)
    ALBUM_ID = rep.json()['data']['album_list'][0]['album_id']
    print ALBUM_ID 

if __name__ == '__main__':
    from pprint import pprint
    pprint(wblogin(USER_ID,USER_PWD))

