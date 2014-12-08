# -*- coding: utf-8 -*-

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
ANDROID_VIEW_CLIENT_HOME = os.environ['ANDROID_VIEW_CLIENT_HOME']
sys.path.append(ANDROID_VIEW_CLIENT_HOME + '/src')
from com.dtmilano.android.viewclient import ViewClient, View

PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(PWD, "../")))
jython_lib = '/home/chris/jython2.5.3/Lib'
sys.path.append("%s/site-packages/simplejson-3.6.3-py2.5.egg" % jython_lib)
sys.path.append('/Users/zhaoqifa/tools/jython2.5.3/Lib/site-packages/simplejson-3.6.5-py2.5.egg/')

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from com.android.monkeyrunner.easy import EasyMonkeyDevice, By
from com.android.chimpchat.hierarchyviewer import HierarchyViewer

import re
import time
import logging
LOG_FORMAT = '%(asctime)s %(name)-5s %(levelname)-6s> %(message)s'
logger = logging.getLogger('Agent')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt='%m-%d %H:%M:%S'))
logging.getLogger('Agent').addHandler(console)

import simplejson as json
from optparse import OptionParser
from utils import get_encoded_character
from lib.tools import str_equal, to_unicode, to_str, read_file

BUTTON_LOCATION = {
    'LEFT_UP': (60, 70),
    'RIGHT_UP': (450, 75),

    'MID_DOWN': (240, 750),
    'LEFT_DOWN': (80, 750),
    'RIGHT_DOWN': (450, 750),

    'GROUPS': (300, 230),
    'MY_GROUPS': (100, 150),  # 我的群
    'GROUP_INPUT': (130, 710),
    'NOTICE_ACCEPT': (240, 730),

    'QQ_NAME': (150, 150),
    'QQ_START': (50, 750),
    'INPUT': (165, 760),
    'INPUT_END': (370, 780),
    'PASTE': (165, 725),
    'SEND': (430, 760),
    'REC_SEND': (428, 467),  # 录音界面出来时，SEND按钮的位置
    'MSG_SPACE': (240, 420),  # 录音界面出来后，点击消息的空白位置
    'GROUP_SEARCH': (240, 220),
    'SEARCH_RESULT': (240, 150),
    'SEARCH_CANCEL': (425, 72),
}

HORIZON_MID = 240
DRAG_POS_UP = (HORIZON_MID, 130)
DRAG_POS_DOWN = (HORIZON_MID, 710)

#定义界面对于的Activity，方便快速定位
SCREENS = {
    'SplashActivity': ('CONTACTS', 'MESSAGES'),
    'TroopActivity': 'GROUP_LIST',
    'ChatActivity': 'GROUP_CHAT',
    'ChatSettingForTroop': 'GROUP_INFO',
    'TroopMemberListActivity': 'GROUP_MEMBER',
    'TroopMemberCardActivity': 'GROUP_MEMBER_INFO',
    'TroopNewcomerNoticeActivity': 'GROUP_NOTICE',
    'FriendProfileCardActivity': 'PROFILE_CARD',
}

SCREENS_NEED_FOCUS = ('GROUP_CHAT', 'GROUP_LIST')

SCREEN_SWITCH_ACTION = {
    'MESSAGES': {
        'MESSAGES': None,
        'CONTACTS': ('LEFT_DOWN', 'MESSAGES'),
        'GROUP_LIST': ('LEFT_UP', 'CONTACTS'),
        'GROUP_CHAT': ('LEFT_UP', 'GROUP_LIST'),
        'GROUP_INFO': ('LEFT_UP', 'GROUP_CHAT'),
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
        'GROUP_NOTICE': ('NOTICE_ACCEPT', ''),
        'PROFILE_CARD': ('BACK', 'BACK', 'MESSAGES')
    },
    'CONTACTS': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': None,
        'GROUP_LIST': ('LEFT_UP', 'CONTACTS'),
        'GROUP_CHAT': ('LEFT_UP', 'GROUP_LIST'),
        'GROUP_INFO': ('LEFT_UP', 'GROUP_CHAT'),
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
        'GROUP_NOTICE': ('NOTICE_ACCEPT', ''),
        'PROFILE_CARD': ('BACK', 'BACK', 'MESSAGES')
    },
    'GROUP_LIST': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': ('GROUPS', 'GROUP_LIST'),
        'GROUP_LIST': None,
        'GROUP_CHAT': ('LEFT_UP', 'GROUP_LIST'),
        'GROUP_INFO': ('LEFT_UP', 'GROUP_CHAT'),
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
        'GROUP_NOTICE': ('NOTICE_ACCEPT', ''),
        'PROFILE_CARD': ('BACK', 'BACK', 'MESSAGES')
    },
    'GROUP_CHAT': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': ('GROUPS', 'GROUP_LIST'),
        'GROUP_LIST': ('enter_group', 'GROUP_CHAT'),
        'GROUP_CHAT': None,
        'GROUP_INFO': ('LEFT_UP', 'GROUP_CHAT'),
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
        'GROUP_NOTICE': ('NOTICE_ACCEPT', ''),
        'PROFILE_CARD': ('BACK', 'BACK', 'MESSAGES')
    },
    'GROUP_INFO': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': ('GROUPS', 'GROUP_LIST'),
        'GROUP_LIST': ('enter_group', 'GROUP_CHAT'),
        'GROUP_CHAT': ('RIGHT_UP', 'GROUP_INFO'),
        'GROUP_INFO': None,
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
        'GROUP_NOTICE': ('NOTICE_ACCEPT', ''),
        'PROFILE_CARD': ('BACK', 'BACK', 'MESSAGES')
    },
    'GROUP_MEMBER': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': ('GROUPS', 'GROUP_LIST'),
        'GROUP_LIST': ('enter_group', 'GROUP_CHAT'),
        'GROUP_CHAT': ('RIGHT_UP', 'GROUP_INFO'),
        'GROUP_INFO': ('RIGHT_UP', 'GROUP_MEMBER'),
        'GROUP_MEMBER': None,
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
        'GROUP_NOTICE': ('NOTICE_ACCEPT', ''),
        'PROFILE_CARD': ('BACK', 'BACK', 'MESSAGES')
    },
}


def vc_view_text(view):
    try:
        return view.getText().replace('\xfe', ' ')
    except:
        logger.warning("get viewclient view text failed!")
        return None


def mr_view_text(view):
    try:
        return view.namedProperties.get('text:mText').value
    except:
        logger.warning("get monkeyrunner view text failed!")
        return None


def extract_msg_layout(layout):
    sender, msg = None, None
    for elem in layout.children:
        if elem.getId() == 'id/chat_item_nick_name':
            sender = vc_view_text(elem)[:-1]
        elif elem.getId() == 'id/chat_item_content_layout':
            msg = vc_view_text(elem)
    return sender, msg


class Group(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Agent(object):
    def __init__(self, device):
        logging.basicConfig(datefmt='%m-%d %H:%M:%S', level=logging.DEBUG,
                            format=LOG_FORMAT, filename='logs/%s.log' % device,
                            encoding='utf8', filemode='w')
        self.device_id = device
        logger.info('connect to adb device')
        self.device = MonkeyRunner.waitForConnection(5, self.device_id)
        logger.info('connect to adb device done')
        self.qq = None
        self.nickname = None
        self.groups = {}
        self.interrupt = False

    def load_group_list(self):
        logger.info('load group list')
        group_list_file = "grouplist/%s" % self.qq
        group_list = read_file(group_list_file)
        for group in group_list:
            ginfo = group.split('\t', 1)
            gid = ginfo[0]
            gname = ginfo[1] if len(ginfo) >= 2 else "Unknown"
            self.groups[gid] = Group(gid, gname)
        return 0

    def dump_groups(self):
        group_list_file = "grouplist/%s" % self.qq
        out_fd = open(group_list_file, 'w')
        for g in self.groups.itervalues():
            out_fd.write(g.id)
            out_fd.write('\t')
            out_fd.write(to_str(g.name))
            out_fd.write('\n')
        out_fd.close()

    def gen_groups(self):
        logger.info("遍历群并生成群信息")
        self.interrupt = False
        if not self.goto('CONTACTS'):
            return
        if not self.goto('GROUP_LIST'):
            return
        last_end_group_name = "", ""
        for i in xrange(30):
            if self.interrupt:
                logger.info("生成群列表被中断")
                return
            if i != 0:
                self.drag(1)
            groups = self.extract_groups()
            if not groups:
                continue
            if str_equal(last_end_group_name[0], groups[-2][0]) and \
               str_equal(last_end_group_name[1], groups[-1][0]):
                logger.info("群列表已到底部，扫描完毕，一共发现%s个群",
                            to_str(len(self.groups)))
                break
            last_end_group_name = groups[-2][0], groups[-1][0]
            self.walk_through_groups(groups)

    def group_in_list(self, gname):
        for g in self.groups.itervalues():
            if str_equal(g.name, gname):
                return True
        return False

    def walk_through_groups(self, groups):
        for name, pos in groups:
            if self.interrupt:
                return
            if self.group_in_list(name):
                logger.info("group: %s in list, skip", to_str(name))
                continue
            logger.info("enter: %s", to_str(name))
            if not self.switch_by_pixel('GROUP_LIST', 'GROUP_CHAT',
                                        HORIZON_MID, pos):
                continue
            gname, gid = self.get_group_name_id()
            if gname and gid:
                self.update_groups(gname, gid)
            self.goto('GROUP_LIST')

    def extract_groups(self):
        #troop_list = self.retry_get_vc_view_by_id('id/qb_troop_list_view')
        vc = ViewClient(device=self.device, serialno=self.device_id)
        troop_list = vc.findViewById('id/qb_troop_list_view')
        if troop_list is None:
            logger.error("提取群列表元素失败，已重试!")
            return []
        ret = []
        logger.debug("troop_list children size: %s", len(troop_list.children))
        for gv in troop_list.children:
            #_text = vc_view_text(gv.children[0])
            _text = gv.children[0].getText()
            if _text:  # 排除我创建的群这样的元素
                logger.debug("skip: %s", to_str(_text))
                continue
            #name = vc_view_text(gv.children[1].children[2].children[1])
            name = gv.children[1].children[2].children[1].getText()
            top, height = gv.getY(), gv.getHeight()
            #pos = gv.top + gv.height / 2 + 182
            pos = top + height / 2 + 182
            logger.debug("find troop: %s-->%s %s %s", to_str(name),
                         to_str(top), to_str(height), to_str(pos))
            if pos <= 185:
                logger.debug("DANGER POS: %s", pos)
                continue
            ret.append((name, pos))
        return ret

    def extract_group_info(self):
        #调用这个函数时，需要已经位于群信息界面
        xlist = self.retry_get_vc_view_by_id('id/common_xlistview')
        if not xlist:
            logger.error("提取群信息失败，已重试!")
            return None, None
        nameAndId = xlist.children[0].children[2].children[0].children[1]
        name = vc_view_text(nameAndId.children[0])
        groupId = vc_view_text(nameAndId.children[1].children[0])
        return name, groupId

    def extract_group_msgs(self):
        logger.info("提取群消息")
        listView = self.retry_get_vc_view_by_id('id/listView1')
        if not listView:
            logger.error("提取群消息失败，已重试!")
            return []
        msgs = []
        for layout in listView.children:
            sender, msg = extract_msg_layout(layout)
            if sender and msg:
                # 自己发的消息解析出来sender会是None
                # 纯图片或表情消息解析出来msg会是None
                msgs.append((sender, msg))
        logger.info("提取群消息完成")
        return msgs

    def gen_group_members(self):
        self.goto('GROUP_MEMBER')
        group_members = []
        last_member = None
        while True:
            screen_members = self.extract_group_members()
            if last_member == screen_members[-1]:
                break
            last_member = screen_members[-1]
            group_members.extend(screen_members)
            self.drag(1)
        return group_members

    def extract_group_members(self):
        screen_members = []
        content = self.get_vc_view_by_id('id/content')
        members_list = content.children[0].children[1].children[0].children
        list_top = 113
        for member in members_list:
            if member.height != 79:
                list_top += member.height
                # 为管理员（4人），C(2人)之类的字样。72 / 33
                continue
            member_location = list_top + 79 / 2
            if member_location >= 800:
                continue
            self.switch_by_pixel('GROUP_MEMBER', 'GROUP_MEMBER_INFO',
                                 HORIZON_MID, member_location)
            list_top += 79
            qqid = self.get_member_id()
            if qqid in screen_members:
                continue
            screen_members.append(qqid)
        return screen_members

    def get_member_id(self):
        content = self.get_vc_view_by_id('id/content')
        tmpqqid = ''
        try:
            _view = content.children[0].children[0].\
                children[1].children[2].children[1]
            tmpqqid = vc_view_text(_view)
        except:
            return ''
        qqid = tmpqqid.split(' ')[0]
        print "Info : get the member id %s !" % qqid
        self.goto('GROUP_MEMBER')
        return qqid

    def retry_get_vc_view_by_id(self, id):
        for i in xrange(3):
            ret = self.get_vc_view_by_id(id)
            if ret:
                return ret
        return None

    def retry_get_mr_view_by_id(self, id):
        for i in xrange(3):
            ret = self.get_mr_view_by_id(id)
            if ret:
                return ret
        return None

    def get_vc_view_by_id(self, id):
        try:
            vc = ViewClient(device=self.device, serialno=self.device_id)
            return vc.findViewById(id)
        except:
            logger.warning('get viewclient view by id[%s] failed!', id)
            return None

    def get_mr_view_by_id(self, id):
        try:
            hViewer = self.device.getHierarchyViewer()
            view = hViewer.findViewById(id)
            return view
        except:
            logger.warning('get monkeyrunner view by id[%s] failed!', id)
            return None

    def get_vc_view_text_by_id(self, id):
        view = self.get_vc_view_by_id(id)
        if not view:
            return None
        return vc_view_text(view)

    def get_mr_view_text_by_id(self, id):
        view = self.get_mr_view_by_id(id)
        if not view:
            return None
        return mr_view_text(view)

    def restart_qq(self):
        self.device.shell('am start -n com.tencent.mobileqq/'
                          'com.tencent.mobileqq.activity.SplashActivity')
        time.sleep(0.2)

    def current_activity(self):
        for i in xrange(50):
            try:
                hViewer = self.device.getHierarchyViewer()
                win_name = hViewer.getFocusedWindowName()
                if not win_name.startswith('com.tencent.mobileqq'):
                    self.restart_qq()
                    continue
            except:
                if i % 10 == 0:
                    logger.error("get hierarchy view failed!!!")
                win_name = None
            if win_name is not None:
                return win_name.split('.')[-1]
            time.sleep(0.2)

    def current_screen(self):
        cur_ac = self.current_activity()
        if not cur_ac:
            return None
        screens = SCREENS[cur_ac]
        if isinstance(screens, basestring):
            return screens
        else:
            # 现在一个activity对应多个screen的只有联系人、消息这一个
            # 目前用不到消息那一栏，所以每次到这个activity的时候，点一下联系人
            # 然后汇报位置为CONTACTS
            self.touch_button('MID_DOWN')
            time.sleep(0.5)
            return 'CONTACTS'

    def touch_pixel(self, x, y):
        logger.debug('Touch: %s,%s', x, y)
        self.device.touch(x, y, MonkeyDevice.DOWN_AND_UP)

    def long_touch_pixel(self, x, y, t=1.5):
        self.device.touch(x, y, MonkeyDevice.DOWN)
        time.sleep(t)
        self.device.touch(x, y, MonkeyDevice.UP)

    def touch_button(self, name):
        if 'BACK' in name:
            self.device.shell("input keyevent KEYCODE_BACK")
        else:
            self.touch_pixel(*BUTTON_LOCATION[name])

    def switch_by_pixel(self, cs, es, x, y):
        self.touch_pixel(x, y)
        return self.watch_screen_switch(cs, es)

    def drag_one_screen(self, down):
        if down:
            logger.debug("drag one screen down")
            self.device.press('KEYCODE_PAGE_DOWN')
            #self.device.drag(DRAG_POS_DOWN, DRAG_POS_UP, 0.2, 1)
        else:
            logger.debug("drag one screen up")
            self.device.press('KEYCODE_PAGE_UP')
            #self.device.drag(DRAG_POS_UP, DRAG_POS_DOWN, 0.2, 1)

    def move_to_screen_end(self):
        self.device.press('KEYCODE_MOVE_END')

    def drag(self, pos, log=True):
        if pos == 0:
            return
        if log:
            logger.info("drag screen: %s", pos)
        down = pos > 0
        for i in xrange(abs(pos)):
            self.drag_one_screen(down)
            time.sleep(0.5)

    def set_focus(self):
        self.drag(1, False)

    def validate_input_text_by_vc(self, msg):
        logger.debug('validate msg by vc begin')
        msg_to_send = self.get_vc_view_text_by_id('id/input')
        if not msg_to_send:
            #可能是消息没粘贴上、禁言或者语言输入打开了
            logger.warning("ViewClient查找id/input元素失败")
            send_btn = self.get_vc_view_text_by_id('id/fun_btn')
            if str_equal("切换到文字输入", send_btn):
                logger.debug("语音输入打开了，关闭之")
                self.touch_button('REC_SEND')
                time.sleep(0.5)
                self.touch_button('MSG_SPACE')
            return False, 0
        #消息框有内容了，验证一下对不对
        if not str_equal(msg_to_send, msg):
            logger.warning("要发送的消息[%s]和输入框中的消息[%s]不一致",
                           to_str(msg), to_str(msg_to_send))
            return False, len(msg_to_send)
        return True, 0

    def validate_input_text_by_mr(self, msg):
        logger.debug('validate msg by mr begin')
        msg_to_send = self.get_mr_view_text_by_id('id/input')
        if not msg_to_send:
            #可能是消息没粘贴上、禁言或者语言输入打开了
            logger.warning("Monkeyrunner查找id/input元素失败")
            send_btn = self.get_mr_view_text_by_id('id/fun_btn')
            if str_equal("切换到文字输入", send_btn):
                logger.debug("语音输入打开了，关闭之")
                self.touch_button('REC_SEND')
                time.sleep(0.5)
                self.touch_button('MSG_SPACE')
            return False, 0
        #消息框有内容了，验证一下对不对
        if not str_equal(msg_to_send, msg):
            logger.warning("要发送的消息[%s]和输入框中的消息[%s]不一致",
                           to_str(msg), to_str(msg_to_send))
            return False, len(msg_to_send)
        return True, 0

    def send_group_msg(self, msg):
        logger.info('send msg: %s', to_str(msg))
        get_encoded_character(self.device_id, to_unicode(msg))
        self.wait_screen('GROUP_CHAT')
        logger.debug('send_group_msg copy character done')

        #防止本QQ屏蔽了该群，需要先点击一下，把提示信息消除掉
        time.sleep(0.5)
        self.touch_button('INPUT')
        time.sleep(0.5)

        self.long_touch_pixel(*BUTTON_LOCATION['INPUT'])
        time.sleep(0.2)
        self.touch_button('PASTE')
        logger.debug('send_group_msg click PASTE done')

        #验证输入框中的内容是否和要发送的内容一致
        """
        因为有时候Monkeyrunner取输入框取不到，ViewClient会取到错误的文本
        为了降低出错的概率，同时使用ViewClient和Monkeyrunner来验证消息，
        只要有一个成功，就发送
        """
        #通过ViewClient去验证内容
        status, msg_len1 = self.validate_input_text_by_vc(msg)
        if status:
            self.touch_button('SEND')
            return 0
        logger.error("通过ViewClient验证要发送的内容失败")
        #通过Monkeyrunner去验证内容
        status, msg_len2 = self.validate_input_text_by_mr(msg)
        if status:
            self.touch_button('SEND')
            return 0
        logger.error("通过Monkeyrunner验证要发送的内容失败")

        msg_len = max(msg_len1, msg_len2)
        if msg_len > 0:
            #消息没发送要把残留的消息删掉
            self.delete_msg(msg_len)
        return 1

    def delete_msg(self, length):
        logger.info('delete msg, length: %s', length)
        self.touch_button('INPUT_END')
        time.sleep(0.2)
        for i in xrange(length + 2):   # 多删两次
            self.device.press('KEYCODE_DEL')

    def check_group_msg(self, target):
        # 在'GROUP_CHAT'界面查看是否有指定的消息
        # 先获取第一屏的消息
        logger.info("check group msg: %s", to_str(target))
        for i in xrange(3):
            if i != 0:
                self.drag(-1)
            msgs = self.extract_group_msgs()
            for sender, msg in msgs:
                logger.info("群消息[%s]来自[%s]", to_str(msg), to_str(sender))
                if str_equal(msg, target):
                    logger.info("target msg[%s] found", to_str(target))
                    return {"drag": i, "sender": sender}
        self.move_to_screen_end()
        logger.info("target msg[%s] not found in 3 screens", to_str(target))
        return 1

    def get_group_name_id(self):
        #在GROUP_CHAT界面时，获取group name和id
        logger.info("获取当前群的名字和id")
        if not self.goto('GROUP_INFO'):
            return None, None
        group_name, group_id = self.extract_group_info()
        logger.info("获取到群的名字和id为: %s,%s",
                    to_str(group_name), to_str(group_id))
        self.goto('GROUP_CHAT')
        return group_name, group_id

    def update_groups(self, gname, gid):
        self.groups[gid] = Group(gname, gid)
        try:
            self.dump_groups()
        except:
            logger.warning("dump groups info failed!")

    def cancel_search(self):
        search_cancel = self.retry_get_vc_view_by_id('id/btn_cancel_search')
        if search_cancel and search_cancel.getX() > HORIZON_MID:
            logger.info("取消搜索操作")
            self.touch_button("SEARCH_CANCEL")

    @staticmethod
    def split_group_id(text):
        pro_ids = re.findall(r"(?<=\()\d+?(?=\))", text)
        for _id in pro_ids[::-1]:
            if _id.isdigit():
                return _id
        return None

    def enter_group_by_search(self, gid):
        self.touch_button('GROUP_SEARCH')
        time.sleep(0.5)
        self.device.type(gid)
        time.sleep(0.5)
        search_result = self.retry_get_vc_view_by_id('id/tv_name')

        if not search_result:  # 没有搜索到，点击取消
            logger.error("搜索结果查找id/tv_name失败，可能需要取消搜索")
            self.cancel_search()
            return False
        # 搜索到结果了，验证一下id对不对，结果示例: 北航人在点评(71771261)
        _text = vc_view_text(search_result)
        logger.debug('群搜索结果: %s', to_str(_text))
        _id = self.split_group_id(_text)
        if not _id:
            logger.error("搜索结果[%s]解析群号失败", to_str(_text))
            self.cancel_search()
            return False
        if not str_equal(_id, gid):
            logger.error("搜索结果的群号[%s]和需要进的群号[%s]不一致",
                         to_str(_id), to_str(gid))
            self.cancel_search()
            return False

        #都对了，进群吧
        if not self.switch_by_pixel("GROUP_LIST", "GROUP_CHAT",
                                    *BUTTON_LOCATION["SEARCH_RESULT"]):
            logger.error("点击搜索结果进群失败!!!!")
            self.cancel_search()
            return False
        return True

    def enter_group_v2(self, gid):
        #if gid not in self.groups:
        #    logger.error("群列表中没有该群[%s]的登记信息，不能进", to_str(gid))
        #    return 1  # 暂时不接受进入无记录群的需求
        if gid in self.groups:
            gname = self.groups[gid].name
        else:
            gname = "Unknown"
        logger.info("准备进入群[%s,%s]", to_str(gid), to_str(gname))
        if not self.goto('CONTACTS'):
            return 2
        if not self.goto('GROUP_LIST'):
            return 3
        if not self.enter_group_by_search(gid):
            return 4
        logger.info("进群[%s,%s]成功", to_str(gid), to_str(gname))
        return 0

    def wait_screen(self, expect_screen):
        # 等待模拟器跳转到某个页面
        # 如果超过10s没到指定页面，返回False
        logger.info('wait screen: %s', expect_screen)
        for i in xrange(50):
            cs = self.current_screen()
            if expect_screen == cs:
                logger.info('screen switch succeed!')
                return True
            time.sleep(0.2)
        logger.error('screen switch timeout!')
        return False

    def watch_screen_switch(self, old_screen, expect_screen):
        # 等待模拟器跳转到某个页面
        # 如果超过10s没到指定页面或者跳转到了错误页面，返回False
        logger.info('screen switch from %s to %s', old_screen, expect_screen)
        for i in xrange(50):
            cs = self.current_screen()
            if expect_screen == cs:
                logger.info('screen switch succeed!')
                return True
            elif cs != old_screen:
                # 没有跳转到特定页面不是由于卡顿造成的
                # 而是跳转到了某个不认识的页面
                logger.error('screen switch failed!')
                return False
            time.sleep(0.2)
        logger.error('screen switch timeout!')
        return False

    def watch_activity_switch(self, current, expect):
        logger.info('activity switch from %s to %s', current, expect)
        for i in xrange(20):
            ca = self.current_activity()
            if expect == ca:
                logger.info('activity switch succeed!')
                return True
            elif ca != current:
                # 没有跳转到特定页面不是由于卡顿造成的
                # 而是跳转到了某个不认识的页面
                logger.error('activity switch failed!')
                return False
            time.sleep(0.2)
        logger.error('activity switch timeout!')

    def do_action(self, action, gid):
        """
        action有两种：
        1. 字符串全部大写，表明这是一个BUTTON_LOCATION里面定义的button
        2. 字符串全小写，表明这是一个Agent的method
        """
        if action.isupper():
            self.touch_button(action)
        else:
            method = getattr(self, action)  # 这里不做容错，直接异常比较好
            method(gid)

    def goto(self, screen, gid=None):
        logger.info('goto: %s', screen)
        for i in xrange(8):
            cs = self.current_screen()
            if not cs:
                continue
            logger.debug("current screen: %s", cs)
            if cs == screen:
                logger.info("goto: %s succeed!", cs)
                if cs in SCREENS_NEED_FOCUS and i != 0:
                    self.set_focus()
                return True
            action = SCREEN_SWITCH_ACTION[screen][cs][0:-1]
            expect_screen = SCREEN_SWITCH_ACTION[screen][cs][-1]
            logger.debug("do_action: %s", action)
            if isinstance(action, str):
                self.do_action(action, gid)
            elif isinstance(action, tuple):
                for act in action:
                    self.do_action(act, gid)
            if expect_screen:
                if not self.watch_screen_switch(cs, expect_screen):
                    #有可能是因为进入一些异常界面，自我救赎吧亲
                    self.rescure()
                    return False
            else:
                self.device.shell("input keyevent KEYCODE_BACK")
                #有些按钮点完不一定跳到什么界面，不固定的，
                #比如群通知界面，点完之后是回到原界面，原界面是不固定的
                #直接进入下次循环就行
                pass
        return False

    def rescure(self):
        cs = self.current_screen()
        if not cs:
            return
        if cs != "GROUP_LIST":
            return
        self.cancel_search()

    def goto_device_home(self):
        self.device.press('KEYCODE_HOME', MonkeyDevice.DOWN_AND_UP, '')

    def get_qq_name_id(self):
        cs = self.current_screen()
        if cs != 'PROFILE_CARD':
            self.goto('CONTACTS')
            self.touch_button('LEFT_DOWN')
            time.sleep(0.5)
            self.touch_button('LEFT_UP')
            time.sleep(0.5)
            self.touch_button('QQ_NAME')
            time.sleep(0.5)
        vc = ViewClient(device=self.device, serialno=self.device_id)
        qq_id = vc.findViewById('id/info').getText()
        qq_id = re.sub(r'\D', '', qq_id.strip())
        qq_name_view = self.get_vc_view_by_id('id/common_xlistview').children[0]\
                    .children[0].children[0].children[0]\
                    .children[5].children[2].children[0]
        qq_name = vc_view_text(qq_name_view)

        self.touch_button('LEFT_UP')
        for i in xrange(3):
            if self.watch_activity_switch('FriendProfileCardActivity',
                                          'SplashActivity'):
                break
            self.touch_button('LEFT_UP')

        if self.current_activity() != 'SplashActivity':
            return None, None

        self.touch_pixel(410, 150)
        time.sleep(0.5)
        self.goto('CONTACTS')
        self.qq, self.nickname = int(qq_id), to_str(qq_name)
        return self.qq, self.nickname


def test_gen_group(device):
    agent = Agent(device)
    agent.gen_groups()


def test_check_group(device):
    agent = Agent(device)
    suc_num = 0
    fail_num = 0
    gids = agent.groups.keys()
    for gid in gids:
        try:
            ret = agent.enter_group_v2(gid)
        except:
            ret = 1
        if ret == 0:
            suc_num += 1
        else:
            fail_num += 1
    print "suc_num=%d, fail_num=%d" % (suc_num, fail_num)


def test(device):
    agent = Agent(device)
    print agent.check_group_msg("AAAA")


def test_name_id(device):
    agent = Agent(device)
    print agent.get_qq_name_id()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--device", dest="device")
    parser.add_option("--test", dest="test_action")
    (options, args) = parser.parse_args()

    device = "emulator-%s" % options.device

    test_action = options.test_action
    if test_action == "check_group":
        test_check_group(device)
    elif test_action == "gen_group":
        test_gen_group(device)
    else:
        test_name_id(device)
