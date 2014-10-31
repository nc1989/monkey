#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from time import sleep,time

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from com.android.monkeyrunner.easy import EasyMonkeyDevice, By
from com.android.chimpchat.hierarchyviewer import HierarchyViewer

jython_lib = '/usr/local/Cellar/jython/2.5.3/libexec/Lib'
# jython_lib = '/home/chris/jython2.5.3/Lib'
sys.path.append("%s/site-packages/simplejson-3.6.3-py2.5.egg" % jython_lib)
import simplejson as json

from tools import url_get, url_post, get_local_ip
from utils import get_encoded_character
from msg import Msg

class MonkeyDaemon(object):
    def __init__(self, qq):
        print '-------- MonkeyDaemon __init__ ---------'
        self.qq = qq

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
        if self.get_grouplist() != 0:
            self.get_pure_group_list_monkey()
            if self.groupList != {}:
                self.write_grouplist()
        self.register_monkey()

    def monkey_set_up(self):
        print '------------ monkey_set_up -------------'
        self.device = MonkeyRunner.waitForConnection(5, self.qq['deviceid'])
        self.easy_device = EasyMonkeyDevice(self.device)
        sleep(0.5)
        if not self.device or not self.easy_device:
            print "Error : monkey_set_up failed !"
            sys.exit(-1)
        return 0


    ### basic check steps ###

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
            self.device.drag((550, 1350),(1000, 1350),0.2,1)
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
        for i in range(0,3):
            try:
                common_xlistview = self.get_hierarchy_view_by_id('id/common_xlistview')
                if common_xlistview:
                    break
            except:
                print "Error : failed to parse view id/common_xlistview !"
                continue
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
        # 暂时没有用到，以后单口的时候可能会用到。
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
        # 按照title来判断呢？
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

    ### basic check steps ###


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
        if self.is_info() == 0:
            self.touch_to_leave()
        if self.is_group() == 0:
            self.touch_to_leave()
        if self.is_grouplist() == 0:
            self.touch_to_leave()
        if self.is_3_columns() == 0:
            self.touch_to_enter_contacts()
            self.touchByMonkeyPixel(700,500)
            self.touchByMonkeyPixel(300,300)
        if self.is_grouplist() == 0:
            return 0
        else:
            print "Error : failed to touch_to_enter_grouplist !"
            return -1

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
            return ''

    def getDescByMonkeyView(self,view):
        # print '------------ getDescByMonkeyView %s -------------' % view
        try:
            return view.namedProperties.get('accessibility:getContentDescription()').value.encode('utf8')
        except:
            # images
            print 'Error : failed to find desc for view : %s !' % view
            return ''

    ### basic monkey operations ###


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
            sleep(2)
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
        self.device.drag((300, 150),(1000, 150),0.2,1)
        nickname = self.get_hierarchy_view_by_id('id/nickname')
        self.qq['qqName'] = self.getTextByMonkeyView(nickname)
        # if self.touchByMonkeyPixel(1050,700) != 0:
        #     return -1
        self.device.drag((1000, 150),(300, 150),0.2,1)
        return 0

    def get_grouplist(self):
        if not os.path.isfile(self.qq['grouplistfile']):
            return 1
        f = open(self.qq['grouplistfile'],'r')
        self.groupList = json.loads(f.read())
        f.close()
        return 0

    def write_grouplist(self):
        if not os.path.isfile(self.qq['grouplistfile']):
            os.system('touch %s' % self.qq['grouplistfile'])
        f = open(self.qq['grouplistfile'],'w')
        f.write(json.dumps(self.groupList).encode('utf8'))
        f.close()
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
                    self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
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

            index = 0
            for group in _groupList:
                index += 1
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
                    'index':index,
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
                    if self.is_group() == 0:
                        for i in range(0,3):
                            groupId = self.get_group_id()
                            if groupId == '':
                                continue
                            else:
                                break
                if groupId == '':
                    print "Error : failed to get the group id for group %s !" % \
                        item['groupName']
                    continue
                else:
                    if groupId in self.groupList.keys():
                        print "Info : this group %s %s has already exist !" % \
                            (item['groupName'],groupId)
                        continue
                self.groupList[groupId] = item
                print "Info : group info: %s , %s , %s , %s, %s !" % \
                    (item['groupName'],groupId,item['drag'],item['index'],item['UILocation'])

        print "Info : total group count : %s !" % len(self.groupList)
        for key in self.groupList:
            print "Info : group info: %s , %s , %s , %s, %s !" % \
                (self.groupList[key]['groupName'],key,self.groupList[key]['drag'], \
                    self.groupList[key]['index'],self.groupList[key]['UILocation'])
        
        self.groupListUpdating = 0
        return 0

    # 获取groupId,结束后仍退出至group
    def get_group_id(self):
        # 此时位于群组会话中，点击进入到群组信息里边
        groupId = ''
        if self.touch_to_enter_info() != 0:
            return ''
        if self.is_info() != 0:
            print "Error : I am not in the info !"
            return ''
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
            'qq': self.qq['qqId'],
            'qqName': self.qq['qqName'],
            'url':self.qq['url'],
            'groupList': json.dumps(groupList)
        }
        url_post(self.qq['robot_url'], data)
        return 0

    def heartbeat_monkey(self):
        print '------------ heartbeat_monkey ------------'
        self.touchByMonkeyPixel(430,150)
        groupList = [{'groupId': key, 'groupName': value['groupName']}
                     for key, value in self.groupList.iteritems()]
        data = {
            'cmd': 'heartbeat',
            'qq': self.qq['qqId'],
            'qqName': self.qq['qqName'],
            'url':self.qq['url'],
            'groupList': json.dumps(groupList)
        }
        url_post(self.qq['robot_url'], data)
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
                if self.heartbeat == 1200:
                    # self.get_pure_group_list_monkey()
                    # if self.groupList != {}:
                        # self.write_grouplist()
                    self.heartbeat_monkey()
                    self.heartbeat = 0
            else:
                self.heartbeat = 0


    ### api for robot manager ###

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
        
        # 这两个大概13～15s ---
        # if self.is_current_group() == 0:
        #     return 0
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
                self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
                # sleep(1)

        # 现在，前，后的顺序查找三个界面
        for j in range(0,3):
            # 大概1s
            if self.is_grouplist() != 0:
                if self.is_info() == 0:
                    self.touch_to_leave()
                if self.is_group() == 0:
                    self.touch_to_leave()
            if possibleDrag == 0:
                if j != 0:
                    # 向下drag一次
                    self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
            else:
                if j == 1:
                    # 向上drag一次
                    self.device.drag((1080/2, 400),(1080/2, 1700),0.2,1)
                if j == 2:
                    # 向下drag一次
                    self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
                    self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)

            # 每次j==0的时候，首先看下possibleUILocation对应的group
            if j == 0:
                try:
                    # 6s
                    if self.touchByMonkeyPixel(1080/2,possibleUILocation) == 0:
                        if self.is_group() == 0:
                            groupId = self.get_group_id()
                except:
                    print "Error : failed to parse the possibleUILocation group !"
                if groupId == data['group']:
                    self.currentGroup['UILocation'] = possibleUILocation
                    return 0
                else:
                    # 不是这个群，就退出至grouplist界面
                    print "Info : failed to enter group %s via possibleDrag %s , possibleUILocation %s !" % \
                            (data['group'], possibleDrag, possibleUILocation)                    
                    if self.is_info() == 0:
                        self.touch_to_leave()
                    if self.is_group() == 0:
                        self.touch_to_leave()   

            # < 1s
            qb_troop_list_view = self.get_hierarchy_view_by_id('id/qb_troop_list_view')
            if qb_troop_list_view == None:
                continue
            _groupList = []
            # 很快
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
                # 2s ---
                if self.is_info() == 0:
                    self.touch_to_leave()
                # 1s
                if self.is_group() == 0:
                    self.touch_to_leave()
                # 1s
                if self.is_grouplist() != 0:
                    break
                # 我创建的群(16) 这样的一行
                notGroup = self.getTextByMonkeyView(group.children[0])
                if notGroup:
                    continue

                # 先根据群名称来查找
                groupNameView = group.children[1].children[2].children[1]
                groupName = self.getTextByMonkeyView(groupNameView)
                if groupName != self.groupList.get(data['group']).get('groupName'):
                    continue

                # 363 is qb_troop_list_view.top, 156是整个一条group的高度。                    
                UILocation = group.top + 156/2 + 363
                # groupName对了，然后看groupId。暂时不要去解析groupName，耗时
                # 第一个和最后一个群组的uilocation需要额外处理，以防点到屏幕外边去了。
                if UILocation < 370 or UILocation > 1760:
                    print "Info : skip this group in case we touch screen incorrectly !"
                    continue
                # 0.5s
                if self.touchByMonkeyPixel(1080/2,UILocation) == 0:
                    if self.is_group() == 0:
                        # 5s ---
                        # 可先判断groupName，相同再进去获取id；否则leave.
                        # 但是会出错。
                        groupId = self.get_group_id()
                    if groupId == data['group']:
                        if j == 1:
                            self.groupList[groupId]['drag'] = possibleDrag - 1
                        elif j == 2:
                            self.groupList[groupId]['drag'] = possibleDrag + 1
                        # 暂未更新drag？
                        self.currentGroup['UILocation'] = UILocation
                        self.groupList[groupId]['UILocation'] = UILocation
                        return 0
        print "Error : failed to enter group %s !" % data['group']
        return -1

    def send_msg(self,data):
        print '\n------------ send_msg ------------'
        if not data.get('msg'):
            return -1        
        # if self.is_current_group() != 0:
        #     return -1

        get_encoded_character(self.qq['deviceid'], data['msg'].decode('utf8'))
        # self.restart_qq_monkey()

        self.easy_device.touch(By.id("id/input"), self.easy_device.DOWN)
        sleep(0.5)
        self.easy_device.touch(By.id("id/input"), self.easy_device.UP)
        self.touchByMonkeyPixel(270,1590)
        # 1s
        inputid = self.get_hierarchy_view_by_id('id/input')
        if inputid:
            text = self.getTextByMonkeyView(inputid)
            print "Info : get msg %s from clipboard !" % text
            if text.strip().split() == data['msg'].strip().split():
                # 1s
                if self.touchByMonkeyId('id/fun_btn') != 0:
                # if self.touchByMonkeyPixel(970,1700) != 0:
                    return -1
            else:
                delete_code = "input keyevent KEYCODE_DEL"
                inputid = self.get_hierarchy_view_by_id('id/input')
                self.touchByMonkeyId('id/input')
                while( self.getTextByMonkeyView(inputid) ):
                    print "Info : delete the incorrect string !"
                    for i in range(0,20):
                        self.device.shell(delete_code)
                    inputid = self.get_hierarchy_view_by_id('id/input')
        print "Info : send msg %s !" % data['msg']
        return 0

    def get_msgs(self,data):
        print '\n------------ get_msgs ------------'
        # if self.is_current_group() != 0:
        #     ret = []
        #     return ret
        # 针对新消息的提示处理,滑动也无效。
        # for i in range(0,3):
        #     self.device.drag((1080/2, 1550),(1080/2, 500),0.1,1)
        # self.touch_to_leave()
        # if self.touchByMonkeyPixel(1080/2,self.currentGroup['UILocation']) != 0:
        #     return []

        self.currentGroup['msgs'] = []
        dragCount = 3
        msgs = []
        # is_stop_drag = 0
        for msgDrag in range(0, dragCount):
            # if is_stop_drag:
                # break
            if msgDrag !=0:
                self.device.drag((1080/2, 500),(1080/2, 1550),0.1,1)

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
                        # < 1s
                        layoutLeft = t.namedProperties.get('layout:mLeft').value.encode('utf8')
                        if layoutLeft == '930':
                            break
                    if t.id == 'id/chat_item_nick_name':
                        item['nickname'] = self.getTextByMonkeyView(t)
                    if t.id == 'id/chat_item_content_layout':
                        item['content'] = self.getTextByMonkeyView(t)
                # 自己发送的消息
                if layoutLeft == '930':
                    continue
                else:
                    if item['nickname'].endswith(':'):
                        item['nickname'] = item['nickname'][0:-1]

                # #此处时间暂不考虑如 Friday 10:46 的情况
                # c = self.getDescByMonkeyView(m)
                # item['time'] = c[0:c.find(' ')]
                
                # 添加每条消息的drag次数
                item['drag'] = msgDrag

                # # 已存储的消息，则没有必要往前drag了。
                # # if item in self.currentGroup['storedMsgs']:
                # #     is_stop_drag = 1
                # #     break
                # store_this_msg = 0
                # for i in self.currentGroup['storedMsgs']:
                #     if i['content'] == item['content'] and i['nickname'] == item['nickname']:
                #         # is_stop_drag = 1
                #         store_this_msg = 1
                #         break
                # if store_this_msg == 1:
                #     continue
                # # 逻辑上有些问题
                # # if is_stop_drag == 1:
                #     # break
                # 未存储，则为新消息.如前一次drag已得到，则跳过.
                has_this_msg = 0
                for j in msgs:
                    if j['content'] == item['content'] and j['nickname'] == item['nickname']:
                        has_this_msg = 1
                        break
                if has_this_msg == 1:
                    continue
                msgs.append(item)
        while(msgDrag>0):
            self.device.drag((1080/2, 1550),(1080/2, 500),0.1,1)
            msgDrag -= 1

        if msgs:
            self.currentGroup['msgs'] = msgs
            print "Info : new msgs count : %s !" % len(msgs)
            for m in self.currentGroup['msgs']:
                print m['nickname'], m['content'], m['drag']
            # default: store the last 10 msgs
            self.currentGroup['storedMsgs'] += self.currentGroup['msgs']            
            print 'Info : stored msgs count ', len(self.currentGroup['storedMsgs'])
            if len(self.currentGroup['storedMsgs']) > 10:
                self.currentGroup['storedMsgs'] = self.currentGroup['storedMsgs'][-10:]
            self.groupList[self.currentGroup['groupId']]['storedMsgs'] = self.currentGroup['storedMsgs']
            # for n in self.currentGroup['storedMsgs']:
                # print n['nickname'], n['content']
      
        return self.currentGroup['msgs']                

    ### api for robot manager ###