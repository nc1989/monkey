#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from time import sleep
import requests
import json

class role():
    def __init__(self,url):
        self.url = url
        self.msgs = []

    def enter_group(self,group):
        data = {
            'cmd':'enter_group',
            'group':group,
        }
        return post(self.url,data)

    def send_msg(self,msg):
        data = {
            'cmd':'send_msg',
            'msg':msg
        }
        return post(self.url,data)

    def get_msgs(self):
        data = {
            'cmd':'get_msgs'
        }
        return post(self.url,data)

def post(url,data):
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=data, headers=headers)
    return response.json()

def two(msga,msgb):
    print "\nInfo : two start"
    print "A : send msg",msga
    a.send_msg(msga)
    print "B : get msgs"
    b.msgs = b.get_msgs()
    for m in b.msgs['data']:
        print m['nickname'],m['time'],m['content']
    print "B : send msg",msgb
    b.send_msg(msgb)
    a.msgs = a.get_msgs()
    print "A : get msgs"
    for m in a.msgs['data']:
        print m['nickname'],m['time'],m['content']
    sleep(1)

if __name__ == '__main__':
    url_a = 'http://0.0.0.0:8001/net_command'
    url_b = 'http://0.0.0.0:8002/net_command'
    print "Info : start two people now !"

    # qqs 3067487368 3040493963
    # groups 17036701   17036754
    # monkeyrunner monkey/monkeyDaemon_3.py --qq 3067487368 --port 8001 --role a
    # monkeyrunner monkey/monkeyDaemon_3.py --qq 3040493963 --port 8002 --role b

    # qqs 2902424837 2195356784
    # groups 397070641 390048779 384048199 361394670
    # monkeyrunner monkey/shaozi.py --qq 2902424837 --port 8001 --role a
    # monkeyrunner monkey/coffee.py --qq 2195356784 --port 8002 --role b

    global a
    a = role(url_a)
    global b
    b = role(url_b)

    group = '384048199'
    #a.enter_group(group)
    #a.send_msg('okey , 我准备晚上出去吃饭     要不要一起啊?')
#

    group = '384048199'
    print ">>>Info : A B enter_group",group
    a.enter_group(group)
    b.enter_group(group)
    two('hello,  大家好嘛','haha,  你又来了!')
    sleep(1)

    group = '361394670'
    print ">>>Info : A B enter_group",group
    a.enter_group(group)
    b.enter_group(group)
    two('hello,  大家好嘛','haha,  你又来了!')
    sleep(1)

    # two('if','else')
    # two('you','me')
    # two('him','her')
    # two('c','d')
    # two('e','f')
    # two('g','h')
    # two('i','j')






