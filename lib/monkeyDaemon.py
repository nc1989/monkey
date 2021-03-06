#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from time import sleep,time

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from com.android.monkeyrunner.easy import EasyMonkeyDevice, By
from com.android.chimpchat.hierarchyviewer import HierarchyViewer

# jython_lib = '/usr/local/Cellar/jython/2.5.3/libexec/Lib'
jython_lib = '/home/chris/jython2.5.3/Lib'
sys.path.append("%s/site-packages/simplejson-3.6.3-py2.5.egg" % jython_lib)
import simplejson as json

from tools import url_get, url_post, get_local_ip
from utils import get_encoded_character
from msg import Msg

class MonkeyDaemon(object):
    def __init__(self, qq):
        print '-------- MonkeyDaemon __init__ ---------'
        self.qq = qq

        # self.emulator = {
        #     'width':1080,
        #     'height':1920,
        #     'qqStart':[150,1650],
        #     'qqName':[75,150],
        #     'msgs':[200,1700],
        #     'contacts':[500,1700],
        #     'groups':[700,500],
        #     'myGroups':[300,300],
        #     'info':[1000,150],
        #     'heartbeat':[430,150],
        #     'paste':[270,1590],
        #     'leave':[150,150],
        #     'self_msg':'930',
        # }

        self.emulator = {
            'width':480,
            'height':800,
            'qqStart':[50,750],
            'qqName':[40,75],
            'msgs':[80,750],
            'contacts':[240,750],
            'groups':[300,230],
            'myGroups':[100,150],
            'info':[450,75],
            'heartbeat':[200,75],
            'paste':[150,725],
            'leave':[60,70],
            'input':[200,760],
            'send':[430,760],
            'self_msg':'404',
        }
        self.path_dict = {
            'is_grouplist':{
                'is_main' : ['contacts','groups'],
                'is_grouplist': 'leave', # 重新进入grouplist
                'is_group': 'leave',
                'is_info' : 'leave',
            },
            'is_group':{
                'is_main': 'is_grouplist',
                'is_grouplist':'enter_group',
                'is_group': None,
                'is_info': 'leave',
            },
            'is_info':{
                'is_main': 'is_grouplist',
                'is_grouplist':'enter_group',
                'is_group': 'info',
                'is_info': None,
            },
            'is_main':{
                'is_home_screen': 'qqStart',
                'is_main': None,
                'is_grouplist': 'leave',
                'is_group': 'leave',
                'is_info': 'leave',
            },
        }
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
        if self.get_qqName_monkey() != 0:
            sys.exit(-1)
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
        try:
            if 'Keyguard' not in self.get_focus_window_name():
                return 0
            else:
                self.screenUsing = 1
                self.device.drag((240, 550),(450, 550),0.2,1)
                self.screenUsing = 0
        except:
            print "Error : failed to get focus window name Keyguard !"
            return -1

    def is_home_screen(self):
        try:
            if 'Launcher' in self.get_focus_window_name():
                return 0
        except:
            print "Error : failed to get focus window name Launcher !"
            return 1

    def is_main(self):
        try:
            if 'SplashActivity' in self.get_focus_window_name():
                return 0
        except:
            print "Error : failed to get focus window name SplashActivity !"
            return 1

    def is_group(self):
        try:
            if 'ChatActivity' in self.get_focus_window_name():
                return 0
        except:
            print "Error : failed to get focus window name ChatActivity !"
            return 1

    def is_info(self):
        try:
            if 'ChatSettingForTroop' in self.get_focus_window_name():
                return 0
        except:
            print "Error : failed to get focus window name ChatSettingForTroop !"
            return 1

    def is_grouplist(self):
        try:
            if 'TroopActivity' in self.get_focus_window_name():
                return 0
        except:
            print "Error : failed to get focus window name TroopActivity !"
            return 1

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

    ### basic check steps ###


    ### basic monkey operations ###

    def get_hierarchy_view_by_id(self,id):
        try:
            hViewer = self.device.getHierarchyViewer()
            view = hViewer.findViewById(id)
            return view
        except:
            return None

    def get_focus_window_name(self):
        try:
            hViewer = self.device.getHierarchyViewer()
            window_name = hViewer.focusedWindowName
            return window_name
        except:
            return ''

    def get_current_view(self):
        window_name = self.get_focus_window_name()
        if 'ChatActivity' in window_name: ### NoneType' object is not iterable
            return 'is_group'
        elif 'TroopActivity' in window_name:
            return 'is_grouplist'
        elif 'SplashActivity' in window_name:
            return 'is_main'
        elif 'ChatSettingForTroop' in window_name:
            return 'is_info'
        elif 'Launcher' in window_name:
            return 'is_home_screen'            
        else:
            return ''

    def goto_window(self,dest):
        print "------------ goto_window %s" % dest
        current_view = self.get_current_view()
        while( current_view != dest ):
            action = self.path_dict[dest][current_view]
            if callable(action):
                action()
            elif 'is_' in action:
                pass
                # action = self.path_dict[dest][current_view]
            elif type(action) is list:
                for i in action:
                    self.touchByMonkeyPixel(self.emulator[i])
            else:
                self.touchByMonkeyPixel(self.emulator[action])
            sleep(1)
            current_view = self.get_current_view()
        return 0

    # decorator to wait screen
    def touch_wait_screen(func):
        def new_func(self, *args):
            if self.screenUsing == 1:
                print "Info : self.screenUsing == 1 !"
                # sleep(1)
            return func(self, *args)
        return new_func

    def drag_to_page_down(self):
        try:
            # self.device.shell("input keyevent KEYCODE_PAGE_DOWN")
            # self.device.press('KEYCODE_PAGE_DOWN','DOWN_AND_UP','')
            self.device.drag((480/2, 710),(480/2, 130),0.2,1)
        except:
            print "Error : failed to drag_to_page_down !"
            return -1

    def drag_to_page_up(self):
        try:
            # self.device.shell("input keyevent KEYCODE_PAGE_UP")
            # self.device.press('KEYCODE_PAGE_UP','DOWN_AND_UP','')
            self.device.drag((480/2, 130),(480/2, 710),0.2,1)
        except:
            print "Error : failed to drag_to_page_up !"
            return -1

    def touch_to_enter_home_screen(self):
        self.device.press('KEYCODE_HOME','DOWN_AND_UP','')
        while(self.is_home_screen() != 0):
            self.device.press('KEYCODE_HOME','DOWN_AND_UP','')

    # @touch_wait_screen
    def touch_to_leave(self):
        try:
            self.touchByMonkeyPixel(self.emulator['leave'])
            return 0
        except:
            print "Error : failed to touch_to_leave !"
            return 1

    def touch_to_enter_main(self):
        # 先回到chatlist或contacts
        return self.goto_window('is_main')

    # @touch_wait_screen
    def touch_to_enter_group(self):
        return self.goto_window('is_group')

    # @touch_wait_screen
    def touch_to_enter_info(self):
        return self.goto_window('is_info')

    # @touch_wait_screen
    # 换另外一个group，要重新进入grouplist
    def touch_to_enter_grouplist(self):   
        return self.goto_window('is_grouplist')

    # @touch_wait_screen
    def touch_to_enter_msgs(self):
        if self.touch_to_enter_main() == 0:
            if self.touchByMonkeyPixel(self.emulator['msgs']) == 0:
                return self.touchByMonkeyPixel(self.emulator['msgs'])

    # @touch_wait_screen
    def touch_to_enter_contacts(self):
        # 不把touch_to_enter_main()判断放在里边，是为了单独处理QQ restart闪退情况。
        if self.touchByMonkeyPixel(self.emulator['contacts']) == 0:
            return self.touchByMonkeyPixel(self.emulator['contacts'])
        else:
            print "Error : failed to touch_to_enter_contacts !"
            return -1

    # @touch_wait_screen
    def touchByMonkeyPixel(self,point):
        # print '------------ touchByMonkeyPixel %s %s -------------' % (x,y)
        try:
            self.screenUsing = 1            
            self.device.touch(point[0],point[1],'DOWN_AND_UP')
            sleep(0.5)
            self.screenUsing = 0
            return 0
        except:
            # sleep(1)
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
            self.touchByMonkeyPixel(self.emulator['qqStart'])
            sleep(3)
            # 一开始启动，QQ闪退的情况
            if self.is_main() == 0:
                self.touch_to_enter_contacts()
            # 点击联系人，QQ闪退的情况
            sleep(2)
        print "Info : qq has been restarted correctly !"
        return 0

    # @check_qq_status
    def get_qqName_monkey(self):
        print '------------ get_qqName_monkey ------------'
        self.touch_to_enter_msgs()
        # self.device.drag((300, 150),(1000, 150),0.2,1)
        self.touchByMonkeyPixel(self.emulator['qqName'])
        nickname = self.get_hierarchy_view_by_id('id/nickname')
        self.qq['qqName'] = self.getTextByMonkeyView(nickname)
        self.device.drag((410, 70),(150, 70),0.2,1)
        if self.qq['qqName']:
            print "Info : qq name is %s !" % self.qq['qqName']
            return 0
        return -1

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
            return 1
        for drag in range(0,10):
            print "Info : drag for %s time !" % drag
            if drag != 0:
                try:
                    # self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
                    # self.device.drag((480/2, 750),(480/2, 190),0.2,1)
                    self.drag_to_page_down()
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
                view = self.get_current_view()
                if view == 'is_group' or view == 'is_info':
                    self.touch_to_enter_grouplist()
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
                    # 78 / 182
                    'UILocation': group.top + 78/2 + 182,
                    'index':index,
                    'msgs': [],
                    'storedMsgs': []
                }

                # 点击进入到群组会话中，去获取groupId
                # 第一个和最后一个群组的uilocation需要额外处理，以防点到屏幕外边去了。
                # if item['UILocation'] < 370 or item['UILocation'] > 1760:
                if item['UILocation'] < 200 or item['UILocation'] > 760:
                    print "Info : skip this group in case we touch screen incorrectly !"
                    continue
                groupId = ''
                if self.touchByMonkeyPixel([self.emulator['width']/2,item['UILocation']]) == 0:
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

            while(self.is_grouplist() != 0):
                self.touch_to_leave()
        print "Info : total group count : %s !" % len(self.groupList)
        for key in self.groupList:
            print "Info : group info: %s , %s , %s , %s, %s !" % \
                (self.groupList[key]['groupName'],key,self.groupList[key]['drag'], \
                    self.groupList[key]['index'],self.groupList[key]['UILocation'])
        
        self.groupListUpdating = 0
        return 0

    # 获取groupId,结束后仍退出至group 界面
    def get_group_id(self):
        # 此时位于群组会话中，点击进入到群组信息里边
        groupId = ''
        if self.touch_to_enter_info() != 0:
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
        if self.touch_to_enter_group() == 0:
            return groupId

    def get_group_members(self):
        group_members = []
        is_stop_drag = 0
        last_member = None
        while True:
            screen_members = self.extract_group_members()
            if last_member == screen_members[-1]:
                break
            last_member = screen_members[-1]
            group_members.extend(screen_members)
            self.drag_to_page_down()
        print "Info : group_members:",group_members            
        return group_members

    def extract_group_members(self):
        screen_members = []       
        content = self.get_hierarchy_view_by_id('id/content')
        members_list = content.children[0].children[1].children[0].children
        list_top = 113
        for member in members_list:
            if member.height != 79:
                list_top += member.height
                # 为管理员（4人），C(2人)之类的字样。72 / 33
                continue
            member_location = list_top + 79/2
            if member_location >= 800:
                continue
            self.touchByMonkeyPixel([240,member_location])
            list_top += 79
            qqid = self.get_member_id()
            if qqid in screen_members:
                continue
            screen_members.append(qqid)
        return screen_members

    def get_member_id(self):
        qqid = ''
        content = self.get_hierarchy_view_by_id('id/content')
        tmpqqid = ''
        try:
            tmpqqid = content.children[0].children[0].children[1].children[2].children[1].namedProperties.get('text:mText').value.encode('utf8')
        except:
            return ''
        qqid = tmpqqid.split(' ')[0]
        print "Info : get the member id %s !" % qqid
        self.touch_to_leave()
        sleep(1)
        return qqid

    def check_group_by_possible_location(self,target_group):
        target_group_name = self.groupList[target_group]['groupName']
        possibleDrag = self.groupList[target_group]['drag']
        possibleUILocation = self.groupList[target_group]['UILocation']
        print "Info : possibleDrag %s , possibleUILocation %s to enter group %s !" % \
                (possibleDrag, possibleUILocation, target_group)
        if possibleDrag > 0:
            for i in range(0,possibleDrag):
                self.drag_to_page_down()

        if self.touchByMonkeyPixel([self.emulator['width']/2,possibleUILocation]) == 0:
            if self.is_group() == 0:
                for i in range(0,3):
                    groupId = ''
                    groupId = self.get_group_id()
                    if groupId == target_group:
                        self.currentGroup['groupId'] = target_group
                        self.currentGroup['groupName'] = target_group_name
                        return 0
                    elif groupId != '':
                        print "Info : get the incorrect groupid %s !" % groupId
                        break
                    else:
                        print "Info : get the empty groupid !"
                        continue
                print "Info : failed to enter group %s via possibleDrag %s , possibleUILocation %s !" % \
                        (target_group, possibleDrag, possibleUILocation)
                # 不是这个群，就退出至grouplist界面,然后查找一下当前界面的groups
                view = self.get_current_view()
                if view == 'is_group' or view == 'is_info':
                    self.touch_to_enter_grouplist()
                if self.find_target_group_from_list(target_group) == 0:
                    return 0
                return 3

    def find_target_group_from_list(self,target_group):
        print '------------ find_target_group_from_list ------------'
        if self.is_grouplist() != 0:
            return -1
        target_group_name = self.groupList[target_group]['groupName']
        # < 1s
        qb_troop_list_view = self.get_hierarchy_view_by_id('id/qb_troop_list_view')
        if qb_troop_list_view == None:
            return -1
        _groupList = []
        _groupList = qb_troop_list_view.children
        if _groupList == []:
            print "Error : failed to parse view qb_troop_list_view !"
            return -1

        # first one is the search box
        # 通过高度来判断是否是group item（78）。
        # 而enter_group时通过名字来查找，不需要此步
        # del _groupList[0]
        for group in _groupList:
            # 我创建的群(16) 这样的一行
            notGroup = self.getTextByMonkeyView(group.children[0])
            if notGroup:
                continue

            # 先根据群名称来查找
            groupNameView = group.children[1].children[2].children[1]
            groupName = self.getTextByMonkeyView(groupNameView)
            print "Info : this_group_name : ", groupName
            if groupName != target_group_name.encode('utf8'):
                continue

            # 363 is qb_troop_list_view.top, 156是整个一条group的高度。# 78 / 182
            UILocation = group.top + 78/2 + 182
            # groupName对了，然后看groupId。暂时不要去解析groupName，耗时
            # 第一个和最后一个群组的uilocation需要额外处理，以防点到屏幕外边去了。
            if UILocation < 200 or UILocation > 760:
                print "Info : skip this group in case we touch screen incorrectly !"
                continue
            # 0.5s
            if self.touchByMonkeyPixel([self.emulator['width']/2,UILocation]) == 0:
                if self.is_group() == 0:
                    for i in range(0,3):
                        groupId = ''
                        groupId = self.get_group_id()
                        if groupId == target_group:
                            self.currentGroup['groupId'] = target_group
                            self.currentGroup['groupName'] = target_group_name
                            self.groupList[target_group]['UILocation'] = UILocation
                            return 0
                        elif groupId != '':
                            print "Info : get the incorrect groupid %s !" % groupId
                            break
                        else:
                            print "Info : get the empty groupid !"
                            continue
        print "Error : failed to find the target group",target_group
        return -1

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
        self.touchByMonkeyPixel(self.emulator['heartbeat'])
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
        t1=time()
        target_group = data['group']
        target_group_name = self.groupList[target_group]['groupName']
        print '------------ enter_group : %s %s' % (target_group_name.encode('utf8'),target_group)

        if self.groupListUpdating == 1:
            print "Info : groupList is updating now ! Please wait about 2 minutes !"
            return 1
        if target_group not in self.groupList:
            print "Error : failed to find in the grouplist %s !" % target_group
            return 2
        # 每次从main界面进入
        self.touch_to_enter_main()
        if self.touch_to_enter_grouplist() != 0:
            print "Error : failed to touch_to_enter_grouplist !"
            return 3
        t_tmp=time()
        print "Info : it takes %s time to enter grouplist" % str(t_tmp-t1)

        # 通过possibleDrag来缩小查找范围。然后从该页的自己、前、后 三个界面查找。
        # 下一步，可以通过possibleIndex，在自己界面进一步缩小查找范围。
        #       在前界面，从后往前查找；在后界面，从前往后查找。

        # 0
        if self.check_group_by_possible_location(target_group) == 0:
            t2=time()
            print "Info : it takes %s time to enter group" % str(t2-t1)
            return 0
        # -1
        # 向上drag一次，possibledrag非0时候
        # self.device.drag((1080/2, 400),(1080/2, 1700),0.2,1)
        view = self.get_current_view()
        if view == 'is_group' or view == 'is_info':
            self.touch_to_enter_grouplist()
        if self.is_grouplist() == 0:
            self.drag_to_page_up()
            if self.find_target_group_from_list(target_group) == 0:
                t2=time()
                print "Info : it takes %s time to enter group" % str(t2-t1)
                return 0
        # 2
        # 向下drag一次
        # self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
        # self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
        view = self.get_current_view()
        if view == 'is_group' or view == 'is_info':
            self.touch_to_enter_grouplist()
        if self.is_grouplist() == 0:        
            self.drag_to_page_down()
            self.drag_to_page_down()
            if self.find_target_group_from_list(target_group) == 0 :
                t2=time()
                print "Info : it takes %s time to enter group" % str(t2-t1)
                return 0
        print "Error : failed to enter group %s !" % target_group
        return -1

    def send_msg(self,data):
        if not data.get('msg'):
            return 1
        msg = data['msg']
        print '------------ send_msg %s' % msg
        print ">>>send_msg 1 ",time()
        if self.is_group() != 0 :
            view = self.get_current_view()
            if view == 'is_info':
                self.touch_to_enter_group()
            else:
                print "Info : I am in the view %s !" % view
                return 1
        print ">>>send_msg 2 ",time()  
        get_encoded_character(self.qq['deviceid'], msg.decode('utf8'))
        # self.restart_qq_monkey()
        print ">>>send_msg 3 ",time()
        # self.easy_device.touch(input_location, self.easy_device.DOWN)
        self.device.touch(self.emulator['input'][0],self.emulator['input'][1],MonkeyDevice.DOWN)
        sleep(1)
        # self.easy_device.touch(input_location, self.easy_device.UP)
        self.device.touch(self.emulator['input'][0],self.emulator['input'][1],MonkeyDevice.UP)
        self.touchByMonkeyPixel(self.emulator['paste'])
        print ">>>send_msg 4 ",time()
        self.touchByMonkeyPixel(self.emulator['send'])
        # # 1s
        # inputid = None
        # try:
        #     inputid = self.get_hierarchy_view_by_id('id/input')
        # except:
        #     print "Error : failed to find view id/input !"
        #     return 2
        # print ">>>send_msg 5 ",time()            
        # if inputid:
        #     text = self.getTextByMonkeyView(inputid)
        #     print "Info : get msg %s from clipboard !" % text
        #     if text.strip().split() == msg.strip().split():
        #         print ">>>send_msg 6 ",time()
        #         # 1s
        #         if self.touchByMonkeyId('id/fun_btn') == 0:
        #         # if self.touchByMonkeyPixel(970,1700) != 0:
        #             print "Info : send msg %s ok !" % msg
        #             print ">>>send_msg 7 ",time()
        #             return 0
        #     else:
        #         delete_code = "input keyevent KEYCODE_DEL"
        #         inputid = self.get_hierarchy_view_by_id('id/input')
        #         self.device.touch(350,750,'DOWN_AND_UP')
        #         while( self.getTextByMonkeyView(inputid) ):
        #             print "Info : delete the incorrect string !"
        #             for i in range(0,20):
        #                 self.device.shell(delete_code)
        #             inputid = self.get_hierarchy_view_by_id('id/input')
        #         print "Error : failed to send msg %s , Incorrect msg !" % msg
        #         return 3

    def get_msgs(self,data):
        print '------------ get_msgs ------------'
        if self.is_group() != 0 :
            view = self.get_current_view()
            if view == 'is_info':
                self.touch_to_enter_group()
            else:
                print "Info : I am in the view %s !" % view
                return 1
        self.currentGroup['msgs'] = []
        dragCount = 3
        msgs = []
        # is_stop_drag = 0
        for msgDrag in range(0, dragCount):
            # if is_stop_drag:
            #     break
            if msgDrag !=0:
                # self.device.drag((1080/2, 500),(1080/2, 1550),0.1,1)
                self.drag_to_page_up()

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
                        if layoutLeft == self.emulator['self_msg']:
                            break
                    if t.id == 'id/chat_item_nick_name':
                        item['nickname'] = self.getTextByMonkeyView(t)
                    if t.id == 'id/chat_item_content_layout':
                        item['content'] = self.getTextByMonkeyView(t)
                # 自己发送的消息
                if layoutLeft == self.emulator['self_msg']:
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
                #         is_stop_drag = 1
                #         store_this_msg = 1
                #         break
                # if store_this_msg == 1:
                #     continue
                # 未存储，则为新消息.如前一次drag已得到，则跳过.
                has_this_msg = 0
                for j in msgs:
                    if j['content'] == item['content'] and j['nickname'] == item['nickname']:
                        has_this_msg = 1
                        break
                if has_this_msg == 1:
                    continue
                msgs.append(item)
        # 针对新消息的提示处理。                
        for i in range(0,4):
            # self.device.drag((1080/2, 1550),(1080/2, 500),0.1,1)
            self.drag_to_page_down()

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
