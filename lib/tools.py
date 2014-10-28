#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import socket

def url_get(url):
    try:
        req = urllib2.Request(url)
        r = urllib2.urlopen(req)
        return r.read()
    except:
        print "Error : Connection refused for url : %s !" % url

def url_post(url, data):
    try:
        req = urllib2.Request(url, urllib.urlencode(data))
        r = urllib2.urlopen(req)
        return r.read()
    except:
        print "Error : Connection refused for url : %s !" % url

def get_local_ip():
    # localIp = socket.gethostbyname(socket.gethostname())
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("dianping.com",80))
    ip_addr = s.getsockname()[0]
    s.close()
    return ip_addr
