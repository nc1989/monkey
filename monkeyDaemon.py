#!/usr/bin/env python
# -*- coding: utf-8 -*-

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from com.android.monkeyrunner.easy import EasyMonkeyDevice, By
from com.android.chimpchat.hierarchyviewer import HierarchyViewer

import os
import sys
import urllib
import urllib2
import socket

from optparse import OptionParser
from time import sleep
from threading import Thread

sys.path.append('/home/chris/jython2.5.3/Lib/site-packages/simplejson-3.6.3-py2.5.egg')
# sys.path.append('/usr/local/Cellar/jython/2.5.3/libexec/Lib/site-packages/simplejson-3.6.3-py2.5.egg')
import simplejson as json

sys.path.append('/home/chris/jython2.5.3/Lib/site-packages/bottle-0.12.7-py2.5.egg')
# sys.path.append('/usr/local/Cellar/jython/2.5.3/libexec/Lib/site-packages/bottle-0.12.7-py2.5.egg')
from bottle import Bottle, run, request, response, get, post

sys.path.append('/home/chris/workspace/qq-marketing/monkey')
import utils

app = Bottle()

emulators={
    '3067487368': '192.168.56.101:5555',
    '2901490931': '192.168.56.101:5555',
    '3040493963': '192.168.56.101:5555',
    '2902424837': '192.168.56.101:5555', # 勺子
    '2195356784': '192.168.56.102:5555', # coffee
}
# robot_url = 'http://0.0.0.0:8017/net_command'
robot_url = 'http://192.168.217.191:8001/net_command'

class MonkeyDaemon(object):
    def __init__(self, options):
        print '-------- MonkeyDaemon __init__ ---------'
        global emulators
        global robot_url

        if options.qq:
            self.qq = options.qq
        if self.qq not in emulators:
            print "Error: can not find the qq in the android ui emulators!"
            sys.exit(-1)
        if options.port:
            self.port = options.port
        if options.role:
            self.role = options.role

        self.qqName = ''
        # add a api to get pure group list, on-going
        self.screenUsing = 0
        self.groupListUpdating = 0
        self.heartbeat = 0
        # {drag, index, groupId, groupName, UILocation, msgs, storedMsgs}
        self.groupList = {}
        # already in this group
        self.currentGroup = {
            'groupId': '',
            'groupName': '',
            'UILocation': '',
            'msgs': [],
            'storedMsgs': []
        }

        self.monkey_set_up()
        if self.restart_qq_monkey() != 0:
            sys.exit(-1)
        self.get_qqName_monkey()
        self.get_pure_group_list_monkey()
        self.register_monkey()

    def monkey_set_up(self):
        print '------------ monkey_set_up -------------'
        devices = os.popen('adb devices').read().strip().split('\n')[1:]
        global deviceid
        deviceid = ''
        if self.role == 'A' or self.role == 'a':
            deviceid = devices[0].split('\t')[0]
        if self.role == 'B' or self.role == 'b':
            deviceid = devices[1].split('\t')[0]
        self.device = MonkeyRunner.waitForConnection(5, deviceid)
        self.easy_device = EasyMonkeyDevice(self.device)
        sleep(0.5)
        if not self.device or not self.easy_device:
            print "Error : monkey_set_up failed !"
            sys.exit(-1)
        return 0

    ### check steps ###

    # decorator to check qq status
    def check_qq_status(func):
        def new_func(self):
            print '------------ check qq status ------------'
            ret = self.is_home_screen()
            if ret == 0:
                return func(self)
            else:
                print "Error : QQ status is not correct !"
                return -1
        return new_func

    def is_screen_lock(self):
        print '------------ is_screen_lock ------------'
        try:
            glow_pad_view = self.get_hierarchy_view_by_id('id/glow_pad_view')
            self.screenUsing = 1
            self.device.drag((550, 1350),(1000, 1350),0.5,1)
            self.screenUsing = 0
            return 0
        except:
            print "Error : failed to parse view id/glow_pad_view !"
            return -1

    def is_home_screen(self):
        # print '------------ is_home_screen ------------'
        launcher = None
        try:
            launcher = self.get_hierarchy_view_by_id('id/launcher')
        except:
            print "Error : failed to parse view id/launcher !"

        if launcher != None:
            return 0
        else:
            return -1

    def is_group(self):
        # print '------------ is_group ------------'
        listView1 = None
        try:
            listView1 = self.get_hierarchy_view_by_id('id/listView1')
        except:
            print "Error : failed to parse view id/listView1 !"
        if listView1:
            # print "Info : already in the group !"
            return 0
        else:
            # print "Info : I am not in the group !"
            return -1

    def is_info(self):
        # print '------------ is_info ------------'
        common_xlistview = None
        try:
            common_xlistview = self.get_hierarchy_view_by_id('id/common_xlistview')
        except:
            print "Error : failed to parse view id/common_xlistview !"
        if common_xlistview:
            # print "Info : already in the info !"
            return 0
        else:
            # print "Info : I am not in the info !"
            return -1

    def is_grouplist(self):
        # print '------------ is_grouplist ------------'
        qb_troop_list_view = None
        try:
            qb_troop_list_view = self.get_hierarchy_view_by_id('id/qb_troop_list_view')
        except:
            print "Error : failed to parse view id/qb_troop_list_view !"
        if qb_troop_list_view:
            # print "Info : already in the grouplist !"
            return 0
        else:
            # print "Info : I am not in the grouplist !"
            return -1

    def is_current_group(self):
        # print '------------ is_current_group ------------'
        print "Info : current group : %s !" % self.currentGroup['groupId']
        groupId = ''
        if self.is_group() == 0:
            groupId = self.get_group_id()
            if self.currentGroup['groupId'] == groupId:
                return 0
            else:
                print "Info : I am not in current group %s, but %s !" % \
                    (self.currentGroup['groupId'], groupId)
                return -1
        else:
            return 1

    def is_3_columns(self):
        # print '------------ is_3_columns ------------'
        recent_chat_list = None
        try:
            recent_chat_list = self.get_hierarchy_view_by_id('id/recent_chat_list')
        except:
            print "Error : failed to parse view id/recent_chat_list !"
        if recent_chat_list:
            # print "Info : already in the 3 columns !"
            return 0
        else:
            # print "Info : I am not in the 3 columns !"
            return -1

    def restart_qq_monkey(self):
        print '------------ restart_qq_monkey -------------'
        while(self.is_home_screen()==0):
            # self.touch_to_enter_home_screen()
            self.touchByMonkeyPixel(150,1650)
            sleep(3)
            # 一开始启动，QQ闪退的情况
            if self.is_3_columns() == 0:
                self.touch_to_enter_contacts()
            # 点击联系人，QQ闪退的情况
        print "Info : qq has been restarted correctly !"
        return 0           
        # if self.is_3_columns() == 0:
        #     return 0
        # elif self.is_grouplist() == 0:
        #     return 0
        # else:
        #     print "Error : failed to restart QQ ! Try again !"
        #     self.touch_to_enter_home_screen()
        #     return -1

    ### check steps ###

    ### basic monkey operations ###

    def get_hierarchy_view_by_id(self,id):
        try:
            hViewer = self.device.getHierarchyViewer()
            view = hViewer.findViewById(id)
            return view
        except:
            # print "Error : failed to get hierarchy view by id %s !" % id
            return None

    # decorator to wait screen
    def touch_wait_screen(func):
        def new_func(self, *args):
            if self.screenUsing == 1:
                print "Info : self.screenUsing == 1 !"
                # sleep(1)
            return func(self, *args)
        return new_func

    def touch_to_enter_home_screen(self):
        try:
            return self.touchByMonkeyPixel(1080/2,1850)
        except:
            print "Error : failed to touch_to_enter_home_screen !"
            return -1            

    # @touch_wait_screen
    def touchByMonkeyId(self,id):
        # print '------------ touchByMonkeyId %s -------------' % id
        try:
            self.screenUsing = 1
            self.easy_device.touch(By.id(id), self.easy_device.DOWN_AND_UP)
            sleep(0.5)
            self.screenUsing = 0
            return 0
        except:
            print 'Error : failed to dump view : %s !' % id
            return -1

    # @touch_wait_screen
    def touch_to_leave(self):
        # print '------------ touch_to_leave -------------'
        try:
            return self.touchByMonkeyPixel(150,150)
        except:
            print "Error : failed to touch_to_leave !"
            return -1

    # @touch_wait_screen
    def touch_to_enter_info(self):
        # print '------------ touch_to_enter_info -------------'
        try:
            return self.touchByMonkeyPixel(1000,150)
        except:
            print "Error : failed to touch_to_enter_info !"
            return -1

    # @touch_wait_screen
    # 换另外一个group，要重新进入grouplist
    def touch_to_enter_grouplist(self):
        print '------------ touch_to_enter_grouplist -------------'
        if self.is_3_columns() == 0:
            self.touch_to_enter_contacts()
            self.touchByMonkeyPixel(700,500)
            self.touchByMonkeyPixel(300,300)
            return 0
        if self.is_info() == 0:
            self.touch_to_leave()
        if self.is_group() == 0:
            self.touch_to_leave()
        self.touch_to_leave()
        self.touch_to_enter_contacts()
        self.touchByMonkeyPixel(700,500)
        self.touchByMonkeyPixel(300,300)
        # if self.is_grouplist():
        #     return 0
        # else:        
        #     print "Error : failed to touch_to_enter_grouplist !"
        #     return -1
        return 0

    # @touch_wait_screen
    def touch_to_enter_msgs(self):
        # 不把is_3_columns()放这里边，是为了单独处理QQ restart闪退情况。
        print '------------ touch_to_enter_msgs -------------'
        if self.touchByMonkeyPixel(300,1700) == 0:
            return self.touchByMonkeyPixel(300,1700)
        else:
            print "Error : failed to touch_to_enter_msgs !"
            return -1

    # @touch_wait_screen
    def touch_to_enter_contacts(self):
        # 不在is_3_columns()判断放在里边，是为了单独处理QQ restart闪退情况。
        print '------------ touch_to_enter_contacts -------------'
        if self.touchByMonkeyPixel(500,1700) == 0:
            return self.touchByMonkeyPixel(500,1700)
        else:
            print "Error : failed to touch_to_enter_contacts !"
            return -1

    # @touch_wait_screen
    def touchByMonkeyPixel(self,x,y):
        # print '------------ touchByMonkeyPixel %s %s -------------' % (x,y)
        try:
            self.screenUsing = 1            
            self.device.touch(x,y,'DOWN_AND_UP')
            sleep(0.5)
            self.screenUsing = 0
            return 0
        except:
            # sleep(1)
            return -1

    def getTextByMonkeyView(self,view):
        # print '------------ getTextByMonkeyView %s -------------' % view
        try:
            return view.namedProperties.get('text:mText').value.encode('utf8')
        except:
            # images
            print 'Error : failed to find text for view : %s !' % view
            return 0

    def getDescByMonkeyView(self,view):
        # print '------------ getDescByMonkeyView %s -------------' % view
        try:
            return view.namedProperties.get('accessibility:getContentDescription()').value.encode('utf8')
        except:
            # images
            print 'Error : failed to find desc for view : %s !' % view
            return 0

    ### basic monkey operations ###


    # @check_qq_status
    def get_qqName_monkey(self):
        print '------------ get_qqName_monkey ------------'
        if self.is_3_columns() == 0:
            self.touch_to_enter_msgs()
        else:
            if self.is_info() == 0:
                self.touch_to_leave()
            if self.is_group() == 0:
                self.touch_to_leave()
            if self.is_grouplist() == 0:
                self.touch_to_leave()
        # if self.touchByMonkeyPixel(90,150) != 0:
        #     return -1
        self.device.drag((300, 150),(1000, 150),0.5,1)
        nickname = self.get_hierarchy_view_by_id('id/nickname')
        self.qqName = self.getTextByMonkeyView(nickname)
        # if self.touchByMonkeyPixel(1050,700) != 0:
        #     return -1
        self.device.drag((1000, 150),(300, 150),0.5,1)
        # print "Info : now monkey daemon is running for %s %s !" % (self.qqName,self.qq)
        return 0

    def get_pure_group_list_monkey(self):
        print '------------ get_pure_group_list_monkey ------------'
        self.groupListUpdating = 1
        if self.touch_to_enter_grouplist() != 0:
            return -1
        for drag in range(0,1):
            if self.is_info() == 0:
                self.touch_to_leave()
            if self.is_group() == 0:
                self.touch_to_leave()
            print "Info : drag for %s time !" % drag
            if drag != 0:
                try:
                    self.device.drag((1080/2, 1700),(1080/2, 400),0.5,1)
                except:
                    print "Error : failed for the %s drag !" % drag

            qb_troop_list_view = self.get_hierarchy_view_by_id('id/qb_troop_list_view')
            if qb_troop_list_view == None:
                continue
            _groupList = []
            _groupList = qb_troop_list_view.children
            if _groupList == []:
                print "Error : failed to parse view qb_troop_list_view !"
                continue

            if drag == 0:
                # first one is the search box
                del _groupList[0]

            for group in _groupList:
                if self.is_info() == 0:
                    self.touch_to_leave()
                if self.is_group() == 0:
                    self.touch_to_leave()
                # 我创建的群(16) 这样的一行
                notGroup = self.getTextByMonkeyView(group.children[0])
                if notGroup:
                    # print "Info : this is not a group %s !" % notGroup
                    continue
                groupNameView = group.children[1].children[2].children[1]
                item = {
                    'groupName': self.getTextByMonkeyView(groupNameView),
                    'drag':drag,
                    # 363 is qb_troop_list_view.top, 156是整个一条group的高度。
                    'UILocation': group.top + 156/2 + 363,
                    'msgs': [],
                    'storedMsgs': []
                }

                # 点击进入到群组会话中，去获取groupId
                # 第一个和最后一个群组的uilocation需要额外处理，以防点到屏幕外边去了。
                if item['UILocation'] < 370 or item['UILocation'] > 1760:
                    print "Info : skip this group in case we touch screen incorrectly !"
                    continue
                groupId = ''
                if self.touchByMonkeyPixel(1080/2,item['UILocation']) == 0:
                    groupId = self.get_group_id()
                if groupId in self.groupList.keys():
                    print "Info : this group %s %s has already exist !" % \
                        (item['groupName'],groupId)
                    continue
                self.groupList[groupId] = item
                print "Info : group info: %s , %s , %s , %s !" % \
                    (item['groupName'],groupId,item['drag'],item['UILocation'])

        print "Info : total group count : %s !" % len(self.groupList)
        for key in self.groupList:
            print "Info : group info: %s , %s , %s , %s !" % \
                (self.groupList[key]['groupName'],key, \
                    self.groupList[key]['drag'],self.groupList[key]['UILocation'])
        
        self.groupListUpdating = 0
        return 0

    # 获取groupId,结束后仍退出至group
    def get_group_id(self):
        # 此时位于群组会话中，点击进入到群组信息里边
        groupId = ''
        if self.is_group() != 0:
            print "Error : I am not in the group !"
            return -1
        if self.touch_to_enter_info() != 0:
            return -1
        if self.is_info() != 0:
            print "Error : I am not in the info !"
            return -1
        for i in range(0,3):       
            try:
                xlist = self.get_hierarchy_view_by_id('id/common_xlistview')
                nameAndId = xlist.children[0].children[2].children[0].children[1]
                groupId = self.getTextByMonkeyView(nameAndId.children[1].children[0])
                break
            except:
                print "Error : failed to get groupId !"
                continue
        print "Info : get this group id : %s !" % groupId
        self.touch_to_leave()
        return groupId

    def register_monkey(self):
        print '------------ register_monkey ------------'
        groupList = [{'groupId': key, 'groupName': value['groupName']} 
                     for key, value in self.groupList.iteritems()]
        data = {
            'cmd': 'register',
            'qq': self.qq,
            'qqName': self.qqName,
            'url': 'http://%s:%s/net_command' % (localIp,self.port),
            'groupList': json.dumps(groupList)
        }
        url_post(robot_url, data)
        return 0

    def monkey_task_loop(self):
        print '------------ monkey_task_loop start ------------'
        # this should never return        
        while(1):
            # if self.is_home_screen() != 0:
                # continue
            sleep(1)
            if self.screenUsing == 0:
                self.heartbeat += 1
                if self.heartbeat == 600:
                    self.get_pure_group_list_monkey()
                    self.heartbeat = 0
            else:
                self.heartbeat = 0


    ### api for robot manager

    # 此处，不考虑UILocation
    def enter_group(self,data):
        print '\n------------ enter_group ------------'
        if self.groupListUpdating == 1:
            print "Info : groupList is updating now ! Please wait about 2 minutes !"
            return 1
        if data['group'] not in self.groupList:
            print "Error : failed to find in the grouplist %s !" % data['group']
            return -1
        if self.currentGroup['groupId'] != data['group']:
            self.currentGroup['groupId'] = data['group']
            self.currentGroup['groupName'] = self.groupList[data['group']]['groupName']
        if self.is_current_group() == 0:
            return 0
        if self.touch_to_enter_grouplist() != 0:
            return -1
        
        groupId = ''
        # 通过possibleDrag来缩小查找范围。然后从该页的自己、前、后 三个界面查找。
        # 下一步，可以通过possibleIndex，在自己界面进一步缩小查找范围。
        #       在前界面，从后往前查找；在后界面，从前往后查找。
        possibleDrag = self.groupList[ data['group'] ]['drag']
        possibleUILocation = self.groupList[ data['group'] ]['UILocation']
        print "Info : possibleDrag %s , possibleUILocation %s to enter group %s !" % \
                (possibleDrag, possibleUILocation, data['group'])
        if possibleDrag > 0:
            for i in range(0,possibleDrag):
                self.device.drag((1080/2, 1700),(1080/2, 400),0.5,1)
                # sleep(1)

        # 现在，前，后的顺序查找三个界面
        for j in range(0,3):
            if self.is_grouplist() != 0:
                if self.is_info() == 0:
                    self.touch_to_leave()
                if self.is_group() == 0:
                    self.touch_to_leave()
            if possibleDrag == 0:
                if j != 0:
                    # 向下drag一次
                    self.device.drag((1080/2, 1700),(1080/2, 400),0.5,1)
            else:
                if j == 1:
                    # 向上drag一次
                    self.device.drag((1080/2, 400),(1080/2, 1700),0.5,1)
                if j == 2:
                    # 向下drag一次
                    self.device.drag((1080/2, 1700),(1080/2, 400),0.5,1)
                    self.device.drag((1080/2, 1700),(1080/2, 400),0.5,1)

            # 每次j==0的时候，首先看下possibleUILocation对应的group
            if j == 0:
                for i in range(0,3):
                    try:
                        if self.touchByMonkeyPixel(1080/2,possibleUILocation) == 0:
                            groupId = self.get_group_id()
                    except:
                        print "Error : failed to parse the possibleUILocation group !"
                    if groupId == data['group']:
                        return 0
                    else:
                        # 不是这个群，就退出至grouplist界面
                        if self.is_info() == 0:
                            self.touch_to_leave()
                        if self.is_group() == 0:
                            self.touch_to_leave()
                        continue                   

            qb_troop_list_view = self.get_hierarchy_view_by_id('id/qb_troop_list_view')
            if qb_troop_list_view == None:
                continue
            _groupList = []
            _groupList = qb_troop_list_view.children
            if _groupList == []:
                print "Error : failed to parse view qb_troop_list_view !"
                continue

            if possibleDrag == 0:
                # first one is the search box
                del _groupList[0]
            elif possibleDrag == 1:
                if j == 1:
                    del _groupList[0]

            for group in _groupList:
                if self.is_info() == 0:
                    self.touch_to_leave()
                if self.is_group() == 0:
                    self.touch_to_leave()
                if self.is_grouplist() != 0:
                    return -1
                # 我创建的群(16) 这样的一行
                notGroup = self.getTextByMonkeyView(group.children[0])
                if notGroup:
                    continue
                # groupNameView = group.children[1].children[2].children[1]
                # groupName = self.getTextByMonkeyView(groupNameView)
                # if groupName != self.groupList.get(data['group']).get('groupName'):
                #     continue

                # 363 is qb_troop_list_view.top, 156是整个一条group的高度。                    
                UILocation = group.top + 156/2 + 363
                # groupName对了，然后看groupId。暂时不要去解析groupName，耗时
                # 第一个和最后一个群组的uilocation需要额外处理，以防点到屏幕外边去了。
                if UILocation < 370 or UILocation > 1760:
                    print "Info : skip this group in case we touch screen incorrectly !"
                    continue
                if self.touchByMonkeyPixel(1080/2,UILocation) == 0:             
                    groupId = self.get_group_id()
                    if groupId == data['group']:
                        return 0
        print "Error : failed to enter group %s !" % data['group']
        return -1

    def send_msg(self,data):
        print '\n------------ send_msg ------------'
        if not data.get('msg'):
            return -1        
        if self.is_current_group() != 0:
            return -1

        utils.get_encoded_character(deviceid, data['msg'].decode('utf8'))
        self.restart_qq_monkey()

        self.easy_device.touch(By.id("id/input"), self.easy_device.DOWN)
        # self.device.touch(500,1700,'DOWN')
        sleep(0.5)
        self.easy_device.touch(By.id("id/input"), self.easy_device.UP)
        # self.device.touch(500,1700,'UP')
        # sleep(1)
        self.touchByMonkeyPixel(270,1590)

        inputid = self.get_hierarchy_view_by_id('id/input')
        if inputid:
            text = self.getTextByMonkeyView(inputid)
            print "Info : get msg %s from clipboard !" % text
            if text.strip().split() == data['msg'].strip().split():
                if self.touchByMonkeyId('id/fun_btn') != 0:
                # if self.touchByMonkeyPixel(970,1700) != 0:
                    return -1
        print "Info : send msg %s !" % data['msg']
        return 0

    def get_msgs(self,data):
        print '\n------------ get_msgs ------------'
        if self.is_current_group() != 0:
            ret = []
            return ret        
        # 针对新消息的提示处理
        for i in range(0,3):
            self.device.drag((1080/2, 1600),(1080/2, 500),0.2,1)

        self.currentGroup['msgs'] = []
        dragCount = 3
        msgs = []
        is_stop_drag = 0
        for msgDrag in range(0, dragCount):
            if is_stop_drag:
                break
            if msgDrag !=0:
                self.device.drag((1080/2, 500),(1080/2, 1600),0.2,1)

            hViewer = None
            _msgs = []
            try:
                listView1 = self.get_hierarchy_view_by_id('id/listView1')
                # 该行会出现AttributeError: 'NoneType' object has no attribute 'children
                _msgs = listView1.children
            except:
                print "Error : failed to parse view : listView1 !"

            # print 'msgs count : ', len(_msgs)-1 #最后一个为输入框
            # reverse()不可用java.Arraylist
            tmpMsgs = []
            for m in _msgs:
                tmpMsgs.insert(0, m)
            for m in tmpMsgs:
                if 'BaseChatItemLayout' not in str(m):
                    continue
                item = {}
                item['nickname'] = ''
                layoutLeft = ''
                for t in m.children:
                    if t.id == 'id/chat_item_head_icon':
                        layoutLeft = t.namedProperties.get('layout:mLeft').value.encode('utf8')
                        if layoutLeft == '930':
                            break
                    if t.id == 'id/chat_item_nick_name':
                        item['nickname'] = self.getTextByMonkeyView(t)
                    if t.id == 'id/chat_item_content_layout':
                        item['content'] = self.getTextByMonkeyView(t)
                if layoutLeft == '930':
                    continue
                else:
                    if item['nickname'].endswith(':'):
                        item['nickname'] = item['nickname'][0:-1]

                #此处时间暂不考虑如 Friday 10:46 的情况
                c = self.getDescByMonkeyView(m)
                item['time'] = c[0:c.find(' ')]
 
                # 已存储的消息，则没有必要往前drag了。
                if item in self.currentGroup['storedMsgs']:
                    is_stop_drag = 1
                    break
                # 未存储，则为新消息.如前一次drag已得到，则跳过。             
                if item in msgs:
                    continue
                msgs.append(item)
        while(msgDrag>0):
            self.device.drag((1080/2, 1600),(1080/2, 500),0.2,1)
            msgDrag -= 1

        if msgs:
            self.currentGroup['msgs'] = msgs
            print "Info : new msgs count : %s !" % len(msgs)
            for m in self.currentGroup['msgs']:
                print m['nickname'], m['content'], m['time']
            # default: store the last 10 msgs
            self.currentGroup['storedMsgs'] += self.currentGroup['msgs']            
            print 'Info : stored msgs count ', len(self.currentGroup['storedMsgs'])
            if len(self.currentGroup['storedMsgs']) > 30:
                self.currentGroup['storedMsgs'] = self.currentGroup['storedMsgs'][-10:]
            self.groupList[self.currentGroup['groupId']]['storedMsgs'] = self.currentGroup['storedMsgs']                
            # for n in self.currentGroup['storedMsgs']:
                # print n['nickname'], n['content'], n['time']
      
        return self.currentGroup['msgs']

    ### api for robot manager

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

def start_listen(port):
    u""" 线程入口，启动bottle开始监听 """
    run(app, host='0.0.0.0', port=int(port))

@app.get('/daemon_info')
def monkey_info():
    print "------------ monkey_info for qq %s %s ------------" % (qqMonkey.qqName,qqMonkey.qq)
    data = {
        'qq': qqMonkey.qq,
        'qqName': qqMonkey.qqName,
        'groupList': qqMonkey.groupList,
        'currentGroup': qqMonkey.currentGroup,
    }
    return json.dumps({"status": 0, "data": data})

# enter_group
# get_msgs
# send_msg
@app.post('/net_command')
def net_command():
    ret = ''
    data = {
        'cmd': request.forms.get('cmd', None),
        'group': request.forms.get('group', None),        
        'msg': request.forms.get('msg', None)
    }
    if not data['cmd']:
        print "Error: cmd is not right!"
        return json.dumps({"status": 1, "err_msg": 'cmd is not right!'})
    if data['cmd'] and hasattr(qqMonkey, data['cmd']):
        print 'Info : dispatch cmd to net_command : ', data['cmd']
        executer = getattr(qqMonkey, data['cmd'])
        if executer:
            ret = executer(data)
            if ret == -1:
                return json.dumps({'status': 1, 'data': ret})
            else:
                return json.dumps({'status': 0, 'data': ret})

# monkeyrunner monkey/monkeyDaemon.py --qq 2901490931 --port 8001 --role a
# monkeyrunner monkey/monkeyDaemon.py --qq 3040493963 --port 8001 --role a
# monkeyrunner monkey/monkeyDaemon.py --qq 3067487368 --port 8001 --role a
# monkeyrunner monkey/monkeyDaemon.py --qq 2195356784 --port 8002 --role b
# monkeyrunner monkey/monkeyDaemon.py --qq 2902424837 --port 8001 --role a
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--qq",    dest="qq")
    parser.add_option("--port",  dest="port")
    parser.add_option("--role",  dest="role")
    (options, args) = parser.parse_args()

    global localIp
    localIp = get_local_ip()

    global qqMonkey
    qqMonkey = MonkeyDaemon(options)
    print '------------Now, Android QQ daemon is running for %s %s on port %s ----------' \
            % (qqMonkey.qqName, qqMonkey.qq, qqMonkey.port)

    th = Thread(target=start_listen, args=[qqMonkey.port])
    th.setDaemon(True)
    th.start()

    qqMonkey.monkey_task_loop()
