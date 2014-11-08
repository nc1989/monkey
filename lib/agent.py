# -*- coding: utf-8 -*-

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from com.android.monkeyrunner.easy import EasyMonkeyDevice, By
from com.android.chimpchat.hierarchyviewer import HierarchyViewer
import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
PWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(PWD, "../")))
jython_lib = '/home/chris/jython2.5.3/Lib'
sys.path.append("%s/site-packages/simplejson-3.6.3-py2.5.egg" % jython_lib)
sys.path.append('/Users/zhaoqifa/tools/jython2.5.3/Lib/site-packages/simplejson-3.6.5-py2.5.egg/')


import time
import logging
LOG_FORMAT = '%(asctime)s %(name)-5s %(levelname)-6s> %(message)s'
logging.basicConfig(datefmt='%m-%d %H:%M:%S', level=logging.DEBUG,
                    format=LOG_FORMAT, filename='agent.log',
                    encoding='utf8', filemode='w')
logger = logging.getLogger('Agent')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt='%m-%d %H:%M:%S'))
logging.getLogger('Agent').addHandler(console)

import simplejson as json
from utils import get_encoded_character
from lib.tools import str_equal, to_unicode, to_str

BUTTON_LOCATION = {
    'LEFT_UP': (60, 70),
    'RIGHT_UP': (450, 75),

    'MID_DOWN': (240, 750),
    'LEFT_DOWN': (80, 750),
    'RIGHT_DOWN': (450, 750),

    'GROUPS': (300, 230),
    'MY_GROUPS': (100, 150),  # 我的群
    'GROUP_INPUT': (130, 710),

    'QQ_NAME': (40, 75),
    'QQ_START': (50, 750),
    'INPUT': (165, 760),
    'INPUT_END': (370, 780),
    'PASTE': (165, 725),
    'SEND': (430, 760),
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
}

SCREEN_SWITCH_ACTION = {
    'MESSAGES': {
        'MESSAGES': None,
        'CONTACTS': ('LEFT_DOWN', 'MESSAGES'),
        'GROUP_LIST': ('LEFT_UP', 'CONTACTS'),
        'GROUP_CHAT': ('LEFT_UP', 'GROUP_LIST'),
        'GROUP_INFO': ('LEFT_UP', 'GROUP_CHAT'),
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
    },
    'CONTACTS': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': None,
        'GROUP_LIST': ('LEFT_UP', 'CONTACTS'),
        'GROUP_CHAT': ('LEFT_UP', 'GROUP_LIST'),
        'GROUP_INFO': ('LEFT_UP', 'GROUP_CHAT'),
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
    },
    'GROUP_LIST': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': ('GROUPS', 'GROUP_LIST'),
        'GROUP_LIST': None,
        'GROUP_CHAT': ('LEFT_UP', 'GROUP_LIST'),
        'GROUP_INFO': ('LEFT_UP', 'GROUP_CHAT'),
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
    },
    'GROUP_CHAT': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': ('GROUPS', 'GROUP_LIST'),
        'GROUP_LIST': ('enter_group', 'GROUP_CHAT'),
        'GROUP_CHAT': None,
        'GROUP_INFO': ('LEFT_UP', 'GROUP_CHAT'),
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
    },
    'GROUP_INFO': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': ('GROUPS', 'GROUP_LIST'),
        'GROUP_LIST': ('enter_group', 'GROUP_CHAT'),
        'GROUP_CHAT': ('RIGHT_UP', 'GROUP_INFO'),
        'GROUP_INFO': None,
        'GROUP_MEMBER': ('LEFT_UP', 'GROUP_INFO'),
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
    },
    'GROUP_MEMBER': {
        'MESSAGES': ('MID_DOWN', 'CONTACTS'),
        'CONTACTS': ('GROUPS', 'GROUP_LIST'),
        'GROUP_LIST': ('enter_group', 'GROUP_CHAT'),
        'GROUP_CHAT': ('RIGHT_UP', 'GROUP_INFO'),
        'GROUP_INFO': ('RIGHT_UP', 'GROUP_MEMBER'),
        'GROUP_MEMBER': None,
        'GROUP_MEMBER_INFO': ('LEFT_UP', 'GROUP_MEMBER'),
    },
}


def get_view_text(view):
    try:
        return view.namedProperties.get('text:mText').value.encode('utf8')
    except:
        return None


def get_view_property(view, property):
    return view.namedProperties.get('layout:mLeft').value.encode('utf8')


def extract_msg_layout(layout):
    sender, msg = None, None
    for elem in layout.children:
        if elem.id == 'id/chat_item_nick_name':
            sender = get_view_text(elem)[:-1]
        elif elem.id == 'id/chat_item_content_layout':
            msg = get_view_text(elem)
    return sender, msg


class Group(object):
    def __init__(self, name, id, drag, pos):
        self.id = id
        self.name = name
        self.drag = drag
        self.pos = pos


class Agent(object):
    def __init__(self, qq, device_id):
        self.qq = qq
        self.device_id = device_id
        logger.info('connect to adb device')
        self.device = MonkeyRunner.waitForConnection(5, device_id)
        logger.info('connect to adb device done')
        #self.easy_device = EasyMonkeyDevice(self.device)
        self.groups = {}
        self.load_groups()

    def load_groups(self):
        group_list_file = "grouplist/%s.grouplist" % self.qq
        if not os.path.exists(group_list_file):
            return
        in_fd = open(group_list_file)
        group_info = json.loads(in_fd.read().strip())
        for k, v in group_info.iteritems():
            self.groups[k] = Group(v['groupName'], k, v['drag'], v['UILocation'])
        in_fd.close()

    def gen_groups(self):
        self.goto('GROUP_LIST')
        for i in xrange(15):
            if i != 0:
                self.drag(1)
            positions = self.extract_groups()
            for name, pos in positions:
                logger.info("enter: %s", name)
                self.touch_pixel(HORIZON_MID, pos)
                time.sleep(0.5)
                self.goto('GROUP_LIST')

    def extract_groups(self):
        troop_list = self.retry_get_view_by_id('id/qb_troop_list_view')
        if troop_list is None:
            logger.error("提取群列表元素失败，已重试!")
            return []
        ret = []
        for gv in troop_list.children:
            if get_view_text(gv.children[0]):  # 排除我创建的群这样的元素
                continue
            name = get_view_text(gv.children[1].children[2].children[1])
            pos = gv.top + gv.height / 2 + 182
            if pos <= 185:
                logger.info("DANGER POS: %s", pos)
                continue
            ret.append((name, pos))
        return ret

    def extract_group_info(self):
        #调用这个函数时，需要已经位于群信息界面
        xlist = self.retry_get_view_by_id('id/common_xlistview')
        if not xlist:
            logger.error("提取群信息失败，已重试!")
            return None, None
        nameAndId = xlist.children[0].children[2].children[0].children[1]
        name = get_view_text(nameAndId.children[0])
        groupId = get_view_text(nameAndId.children[1].children[0])
        return name, groupId

    def extract_group_msgs(self):
        logger.info("提取群消息")
        listView = self.retry_get_view_by_id('id/listView1')
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
        content = self.get_view_by_id('id/content')
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
        content = self.get_view_by_id('id/content')
        tmpqqid = ''
        try:
            _view = content.children[0].children[0].\
                children[1].children[2].children[1]
            tmpqqid = get_view_text(_view)
        except:
            return ''
        qqid = tmpqqid.split(' ')[0]
        print "Info : get the member id %s !" % qqid
        self.goto('GROUP_MEMBER')
        return qqid

    def retry_get_view_by_id(self, id):
        for i in xrange(3):
            ret = self.get_view_by_id(id)
            if ret:
                return ret
        return None

    def get_view_by_id(self, id):
        try:
            hViewer = self.device.getHierarchyViewer()
            view = hViewer.findViewById(id)
            return view
        except:
            logger.warning('get view by id[%s] failed!', id)
            return None

    def get_view_text_by_id(self, id):
        view = self.get_view_by_id(id)
        if not view:
            return None
        return get_view_text(view)

    def current_activity(self):
        for i in xrange(50):
            hViewer = self.device.getHierarchyViewer()
            win_name = hViewer.getFocusedWindowName()
            if win_name is not None:
                return win_name.split('.')[-1]
            time.sleep(0.2)

    def current_screen(self):
        cur_ac = self.current_activity()
        screens = SCREENS[cur_ac]
        if isinstance(screens, basestring):
            return screens
        else:
            # 现在一个activity对应多个screen的只有联系人、消息这一个
            # 目前用不到消息那一栏，所以每次到这个activity的时候，点一下联系人
            # 然后汇报位置为CONTACTS
            self.touch_button('MID_DOWN')
            return 'CONTACTS'

    def touch_pixel(self, x, y):
        logger.debug('Touch: %s,%s', x, y)
        self.device.touch(x, y, MonkeyDevice.DOWN_AND_UP)

    def long_touch_pixel(self, x, y, t=1.5):
        self.device.touch(x, y, MonkeyDevice.DOWN)
        time.sleep(t)
        self.device.touch(x, y, MonkeyDevice.UP)

    def touch_button(self, name):
        self.touch_pixel(*BUTTON_LOCATION[name])

    def switch_by_pixel(self, cs, es, x, y):
        self.touch_pixel(x, y)
        return self.watch_screen_switch(cs, es)

    def drag_one_screen(self, down):
        if down:
            logger.info("drag one screen down")
            self.device.drag(DRAG_POS_DOWN, DRAG_POS_UP, 0.2, 1)
        else:
            logger.info("drag one screen up")
            self.device.drag(DRAG_POS_UP, DRAG_POS_DOWN, 0.2, 1)

    def drag(self, pos):
        down = pos > 0
        for i in xrange(abs(pos)):
            self.drag_one_screen(down)
            time.sleep(0.5)

    def send_group_msg(self, msg, validate=True):
        logger.info('send msg: %s', to_str(msg))
        get_encoded_character(self.device_id, to_unicode(msg))
        self.wait_screen('GROUP_CHAT')
        logger.debug('send_group_msg copy character done')

        if not validate:
            #如果发消息前不验证，那么先删除一下消息发送框的中原有内容
            self.delete_msg(20)

        self.long_touch_pixel(*BUTTON_LOCATION['INPUT'])
        time.sleep(0.2)
        self.touch_pixel(*BUTTON_LOCATION['PASTE'])
        logger.debug('send_group_msg click PASTE done')

        if validate:
            #验证消息
            logger.debug('validate msg begin')
            msg_to_send = self.get_view_text_by_id('id/input')
            if not str_equal(msg_to_send, msg):
                logger.error("要发送的消息[%s]和输入框中的消息[%s]不一致",
                             to_str(msg), to_str(msg_to_send))
                if msg_to_send:  # 消息没发送要把残留的消息删掉
                    self.delete_msg(len(msg_to_send))
                return 1
            logger.debug('validate msg done')

        self.touch_pixel(*BUTTON_LOCATION['SEND'])
        return 0

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
        logger.info("target msg[%s] not found in 3 screens", to_str(target))
        return 1

    def get_group_name_id(self):
        #在GROUP_CHAT界面时，获取group name和id
        logger.info("获取当前群的名字和id")
        if not self.goto('GROUP_INFO'):
            return None, None
        group_name, group_id = self.extract_group_info()
        logger.info("获取到群的名字和id为: %s,%s", to_str(group_name), group_id)
        self.goto('GROUP_CHAT')
        return group_name, group_id

    def update_groups(self, gname, gid, drag, pos):
        self.groups[gid] = Group(gname, gid, drag, pos)

    def enter_group_by_postion(self, gid, drag, pos):
        logger.info("根据位置进群[%s]，drag/pos=%s/%s", gid, drag, pos)
        self.drag(drag)
        if not self.switch_by_pixel('GROUP_LIST', 'GROUP_CHAT',
                                    HORIZON_MID, pos):
            return False
        group_name, group_id = self.get_group_name_id()
        if group_id == gid:  # 成功返回True
            logger.info("群号匹配成功")
            return True
        logger.warning("群号匹配不成功，%s != %s", group_id, gid)

        if group_name and group_id:
            # 失败的话，更新groups信息，防止下次继续出错
            self.update_groups(group_name, group_id, drag, pos)
        self.goto("GROUP_LIST")  # 进群失败，退回到群列表页
        return False

    def enter_group_in_screen(self, gname, gid):
        #解析并验证当前屏幕上的群组
        logger.info("解析当前屏幕所有群")
        screen_groups = self.extract_groups()
        for name, pos in screen_groups:
            if str_equal(name, gname):
                logger.info("发现名字[%s]匹配的群，进入验证群号", to_str(name))
                if self.enter_group_by_postion(gid, 0, pos):
                    logger.info("恭喜，进群成功")
                    return True
        logger.info("当前屏幕没有找到指定群[%s,%s]", gid, to_str(gname))
        return False

    def enter_group_by_finding(self, current_drag, gid):
        if not self.goto("GROUP_LIST"):
            return
        gname = self.groups[gid].name
        logger.info("尝试查找并进入群[%s,%s]", gid, to_str(gname))
        if self.enter_group_in_screen(gname, gid):
            return 0

        #当前屏幕没有找到，往上翻一页去找
        #如果当前屏幕是第一屏，就没有这个必要了
        if current_drag != 0:
            logger.info("往前翻1屏，继续查找")
            self.drag(-1)
            if self.enter_group_in_screen(gname, gid):
                return 0

        #如果当前屏幕的前一屏幕也没有找到，进入后一屏去找
        #如果之前往上翻过一屏了，现在需要往下翻两屏
        drag = 2 if current_drag != 0 else 1
        logger.info("往后翻%s屏，继续查找", gid)
        self.drag(drag)
        if self.enter_group_in_screen(gname, gid):
            return 0

        logger.error("前后1屏都没找到对应群，累死了，不找了")
        return 1

    def enter_group(self, gid):
        logger.info("准备进入群[%s]", gid)
        if gid not in self.groups:
            logger.error("群列表中没有该群的登记信息[%s]，不能进", gid)
            return 1  # 暂时不接受进入无记录群的需求
        if not self.goto('CONTACTS'):
            return 2
        if not self.goto('GROUP_LIST'):
            return 3
        #前面两步操作保证进入的GROUP_LIST页面是没有被向下翻页过的
        group = self.groups[gid]
        drag, pos = group.drag, group.pos
        if self.enter_group_by_postion(gid, drag, pos):
            logger.info("根据位置进群[%s]成功", gid)
            return 0
        logger.info("根据位置进群[%s]失败", gid)
        return self.enter_group_by_finding(drag, gid)

    def wait_screen(self, expect_screen):
        # 等待模拟器跳转到某个页面
        # 如果超过10s没到指定页面，返回False
        logger.info('wait screen: %s', expect_screen)
        for i in xrange(50):
            cs = self.current_screen()
            if expect_screen == cs:
                logger.info('screen switch success!')
                return True
            time.sleep(0.2)
        logger.error('screen switch timeout!')
        return False

    def watch_screen_switch(self, old_screen, expect_screen):
        # 等待模拟器跳转到某个页面
        # 如果超过10s没到指定页面或者跳转到了错误页面，返回False
        logger.info('watch screen switch from %s to %s',
                    old_screen, expect_screen)
        for i in xrange(50):
            cs = self.current_screen()
            if expect_screen == cs:
                logger.info('screen switch success!')
                return True
            elif cs != old_screen:
                # 没有跳转到特定页面不是由于卡顿造成的
                # 而是跳转到了某个不认识的页面
                logger.error('screen switch failed!')
                return False
            time.sleep(0.2)
        logger.error('screen switch timeout!')
        return False

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
            logger.info("current screen: %s", cs)
            if cs == screen:
                logger.info("进入指定页面: %s", cs)
                return True
            action, except_screen = SCREEN_SWITCH_ACTION[screen][cs]
            logger.info("do_action: %s", action)
            self.do_action(action, gid)
            if not self.watch_screen_switch(cs, except_screen):
                return False
        return False

    def goto_device_home(self):
        self.device.press('KEYCODE_HOME', MonkeyDevice.DOWN_AND_UP, '')


if __name__ == "__main__":
    agent = Agent("2902424837", "emulator-5554")
    #print agent.goto('GROUP_LIST')
    #print agent.goto('CONTACTS')
    #print agent.goto_device_home()
    #agent.gen_groups()
    suc_num = 0
    fail_num = 0
    gids = agent.groups.keys()
    for gid in gids:
        try:
            ret = agent.enter_group(gid)
        except:
            ret = 1
        if ret == 0:
            suc_num += 1
        else:
            fail_num += 1
    print "suc_num=%d, fail_num=%d" % (suc_num, fail_num)

    #for i in xrange(50):
    #    print agent.send_group_msg("天命，哈哈哈%s" % i, False)
    #print agent.check_group_msg('不要打岔')
    #print agent.check_group_msg('挺实惠的啊')
    #print agent.check_group_msg('挺实惠的啊123123')
