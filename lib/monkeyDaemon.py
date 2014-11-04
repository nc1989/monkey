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
            'paste':[130,710],
            'leave':[60,70],
            'self_msg':'404',
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
            print "Info : I am already in the grouplist !"
            return 0
        else:
            print "Info : I am not in the grouplist !"
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

    def get_current_view(self):
        try:
            print ">>>1:",time()
            hViewer = self.device.getHierarchyViewer()
            print ">>>2:",time()
            if hViewer.findViewById('id/listView1'):
                print ">>>3:",time()
                print "Info : I am in the view is_group !"
                return 'is_group'
            elif hViewer.findViewById('id/qb_troop_list_view'):
                print "Info : I am in the view is_grouplist !"
                return 'is_grouplist'
            elif hViewer.findViewById('id/elv_buddies'):
                print "Info : I am in the view is_contacts !"
                return 'is_contacts'
            elif hViewer.findViewById('id/common_xlistview'):
                print "Info : I am in the view is_info !"
                return 'is_info'
            elif hViewer.findViewById('id/recent_chat_list'):
                print "Info : I am in the view is_chatlist !"
                return 'is_chatlist'
            else:
                return ''
        except:
            return ''

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
        try:
            # return self.touchByMonkeyPixel(1080/2,1850)
            # self.device.shell("input keyevent KEYCODE_HOME")
            self.device.press('KEYCODE_HOME','DOWN_AND_UP','')
        except:
            print "Error : failed to touch_to_enter_home_screen !"
            return -1            

    # @touch_wait_screen
    def touch_to_leave(self):
        # print '------------ touch_to_leave -------------'
        try:
            self.touchByMonkeyPixel(self.emulator['leave'][0],self.emulator['leave'][1])
            # self.device.shell("input keyevent KEYCODE_BACK")
            # self.device.press('KEYCODE_BACK','DOWN_AND_UP','')
            return 0
        except:
            print "Error : failed to touch_to_leave !"
            return -1

    def touch_to_enter_main(self):
        # 先回到chatlist或contacts        
        print '------------ touch_to_enter_main -------------'
        view = self.get_current_view()
        if view == 'is_chatlist' or view == 'is_contacts':
            print "Info : I am in the main view %s !" % view
        elif view == "is_grouplist":
            self.touch_to_leave()
        elif view == 'is_group':
            self.touch_to_leave()
            self.touch_to_leave()
        elif view == 'is_info':
            self.touch_to_leave()
            self.touch_to_leave()
            self.touch_to_leave()
        else:
            print "Error : failed to touch_to_enter_main !"
            return -1
        return 0

    # @touch_wait_screen
    def touch_to_enter_info(self):
        # print '------------ touch_to_enter_info -------------'
        try:
            return self.touchByMonkeyPixel(self.emulator['info'][0],self.emulator['info'][1])
        except:
            print "Error : failed to touch_to_enter_info !"
            return -1

    # @touch_wait_screen
    # 换另外一个group，要重新进入grouplist
    def touch_to_enter_grouplist(self):
        print '------------ touch_to_enter_grouplist -------------'     
        if self.touch_to_enter_main() != 0:
            return -1
        if self.touch_to_enter_contacts() == 0:
            if self.touchByMonkeyPixel(self.emulator['groups'][0],self.emulator['groups'][1]) == 0:
                if self.is_grouplist() == 0:
                    if self.touchByMonkeyPixel(self.emulator['myGroups'][0],self.emulator['myGroups'][1]) == 0:
                        return 0
        return -1

    # @touch_wait_screen
    def touch_to_enter_msgs(self):
        # 不把is_3_columns()放这里边，是为了单独处理QQ restart闪退情况。
        print '------------ touch_to_enter_msgs -------------'
        if self.touchByMonkeyPixel(self.emulator['msgs'][0],self.emulator['msgs'][1]) == 0:
            return self.touchByMonkeyPixel(self.emulator['msgs'][0],self.emulator['msgs'][1])
        else:
            print "Error : failed to touch_to_enter_msgs !"
            return -1

    # @touch_wait_screen
    def touch_to_enter_contacts(self):
        # 不在is_3_columns()判断放在里边，是为了单独处理QQ restart闪退情况。
        print '------------ touch_to_enter_contacts -------------'
        if self.touchByMonkeyPixel(self.emulator['contacts'][0],self.emulator['contacts'][1]) == 0:
            return self.touchByMonkeyPixel(self.emulator['contacts'][0],self.emulator['contacts'][1])
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
            self.touchByMonkeyPixel(self.emulator['qqStart'][0],self.emulator['qqStart'][1])
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
        if self.touch_to_enter_main() != 0:
            return -1
        self.touch_to_enter_msgs()
        # self.device.drag((300, 150),(1000, 150),0.2,1)
        self.touchByMonkeyPixel(self.emulator['qqName'][0],self.emulator['qqName'][1])
        nickname = self.get_hierarchy_view_by_id('id/nickname')
        self.qq['qqName'] = self.getTextByMonkeyView(nickname)
        # self.device.drag((1000, 150),(300, 150),0.2,1)
        self.touch_to_leave()
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
            return -1
        for drag in range(0,15):
            if self.is_info() == 0:
                self.touch_to_leave()
            if self.is_group() == 0:
                self.touch_to_leave()
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
                if self.touchByMonkeyPixel(self.emulator['width']/2,item['UILocation']) == 0:
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

    # 获取groupId,结束后仍退出至group 界面
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

    def check_group_by_possible_location(self,target_group):
        target_group_name = self.groupList[target_group]['groupName']
        possibleDrag = self.groupList[target_group]['drag']
        possibleUILocation = self.groupList[target_group]['UILocation']
        print "Info : possibleDrag %s , possibleUILocation %s to enter group %s !" % \
                (possibleDrag, possibleUILocation, target_group)
        if possibleDrag > 0:
            for i in range(0,possibleDrag):
                # self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
                self.drag_to_page_down()

        if self.touchByMonkeyPixel(self.emulator['width']/2,possibleUILocation) == 0:
            if self.is_group() == 0:
                # 可先判断groupName，相同再进去获取id；否则leave.
                # 直接去判断groupId。省时间。
                # title_view = self.get_hierarchy_view_by_id('id/title')
                # title = self.getTextByMonkeyView(title_view)
                # print "actual_group_name : %s" % title
                # print "target_group_name : %s" % target_group_name
                # # 以后可以把找到的group的位置更新下
                # if title == target_group_name:
                if self.get_group_id() == target_group:
                    self.currentGroup['groupId'] = target_group
                    self.currentGroup['groupName'] = target_group_name
                    return 0
                else:
                    print "Info : failed to enter group %s via possibleDrag %s , possibleUILocation %s !" % \
                            (target_group, possibleDrag, possibleUILocation)            
                    # 不是这个群，就退出至grouplist界面
                    if self.is_group() == 0:
                        self.touch_to_leave()
                    # 查找一下当前界面的groups
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
            if self.touchByMonkeyPixel(self.emulator['width']/2,UILocation) == 0:
                if self.is_group() == 0:
                    if self.get_group_id() == target_group:
                        self.currentGroup['groupId'] = target_group
                        self.currentGroup['groupName'] = target_group_name
                        self.groupList[target_group]['UILocation'] = UILocation
                        return 0
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
        self.touchByMonkeyPixel(self.emulator['heartbeat'][0],self.emulator['heartbeat'][1])
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
        target_group = data['group']
        target_group_name = self.groupList[target_group]['groupName']
        print '\n------------ enter_group : %s %s' % (target_group_name.encode('utf8'),target_group)

        if self.groupListUpdating == 1:
            print "Info : groupList is updating now ! Please wait about 2 minutes !"
            return 1
        if target_group not in self.groupList:
            print "Error : failed to find in the grouplist %s !" % target_group
            return 2
        
        if self.touch_to_enter_grouplist() != 0:
            print "Error : failed to touch_to_enter_grouplist !"
            return 3

        # 通过possibleDrag来缩小查找范围。然后从该页的自己、前、后 三个界面查找。
        # 下一步，可以通过possibleIndex，在自己界面进一步缩小查找范围。
        #       在前界面，从后往前查找；在后界面，从前往后查找。

        # 0
        if self.check_group_by_possible_location(target_group) == 0:
            return 0
        # -1
        # 向上drag一次，possibledrag非0时候
        # self.device.drag((1080/2, 400),(1080/2, 1700),0.2,1)
        self.drag_to_page_up()
        if self.find_target_group_from_list(target_group) == 0:
            return 0
        # 2
        # 向下drag一次
        # self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
        # self.device.drag((1080/2, 1700),(1080/2, 400),0.2,1)
        self.drag_to_page_down()
        self.drag_to_page_down()
        if self.find_target_group_from_list(target_group) == 0 :
            return 0
        print "Error : failed to enter group %s !" % target_group
        return -1

    def send_msg(self,data):
        if not data.get('msg'):
            return 1
        print '\n------------ send_msg %s' % data['msg']

        get_encoded_character(self.qq['deviceid'], data['msg'].decode('utf8'))
        # self.restart_qq_monkey()

        self.easy_device.touch(By.id("id/input"), self.easy_device.DOWN)
        sleep(0.5)
        self.easy_device.touch(By.id("id/input"), self.easy_device.UP)
        self.touchByMonkeyPixel(self.emulator['paste'][0],self.emulator['paste'][1])
        # 1s
        inputid = self.get_hierarchy_view_by_id('id/input')
        if inputid:
            text = self.getTextByMonkeyView(inputid)
            print "Info : get msg %s from clipboard !" % text
            if text.strip().split() == data['msg'].strip().split():
                # 1s
                if self.touchByMonkeyId('id/fun_btn') == 0:
                # if self.touchByMonkeyPixel(970,1700) != 0:
                    return 0
            else:
                delete_code = "input keyevent KEYCODE_DEL"
                inputid = self.get_hierarchy_view_by_id('id/input')
                self.touchByMonkeyId('id/input')
                while( self.getTextByMonkeyView(inputid) ):
                    print "Info : delete the incorrect string !"
                    for i in range(0,20):
                        self.device.shell(delete_code)
                    inputid = self.get_hierarchy_view_by_id('id/input')
        return 0

    def get_msgs(self,data):
        print '\n------------ get_msgs ------------'

        self.currentGroup['msgs'] = []
        dragCount = 3
        msgs = []
        # is_stop_drag = 0
        for msgDrag in range(0, dragCount):
            # if is_stop_drag:
                # break
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
        # 针对新消息的提示处理。                
        for i in range(0,6):
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