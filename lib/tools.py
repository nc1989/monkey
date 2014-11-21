#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import socket
import os

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

def str_equal(s1, s2):
    if isinstance(s1, unicode):
        s1 = s1.encode('utf8')
    if isinstance(s2, unicode):
        s2 = s2.encode('utf8')
    return s1 == s2

def to_unicode(s):
    if isinstance(s, unicode):
        return s
    return s.decode('utf8')

def to_str(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    return s

def read_file(f):
    if not os.path.isfile(f):
        return []
    with open(f) as in_fd:
        return [l.strip() for l in in_fd]
