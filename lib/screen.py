# -*- coding: utf-8 -*-
import os
import sys
ANDROID_VIEW_CLIENT_HOME = os.environ['ANDROID_VIEW_CLIENT_HOME']
sys.path.append(ANDROID_VIEW_CLIENT_HOME + '/src')
from com.dtmilano.android.viewclient import ViewClient, View
import logging
logger = logging.getLogger('Agent')


#############monkeyrunner和android view client基础操作API
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


def get_vc_view_by_id(device, serialno, id, retry=1):
    for i in xrange(retry):
        try:
            vc = ViewClient(device=device, serialno=serialno)
            ret = vc.findViewById(id)
        except:
            logger.warning('get viewclient view by id[%s] failed!', id)
            ret = None
        if ret:
            return ret


def vc_has_view(vc, id):
    return vc.findViewById(id) is not None


def get_mr_view_by_id(device, id, retry=1):
    for i in xrange(retry):
        try:
            hViewer = device.getHierarchyViewer()
            ret = hViewer.findViewById(id)
        except:
            logger.warning('get monkeyrunner view by id[%s] failed!', id)
            ret = None
        if ret:
            return ret


def get_vc_view_text_by_id(device, serialno, id, retry=1):
    view = get_vc_view_by_id(device, serialno, id, retry)
    if not view:
        return None
    return vc_view_text(view)


def get_mr_view_text_by_id(device, id, retry=1):
    view = get_mr_view_by_id(device, id, retry)
    if not view:
        return None
    return mr_view_text(view)


##############按钮位置定义和屏幕切换操作
HORIZON_MID = 240

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
    'PROFILE_TO_MSG': (410, 150),
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
    "GROUPS_IN_LIST": (120, 147), # 群列表页面上“我的群”按钮
}


class SSA(object):
    """ short for screen switch action """
    __slots__ = ['screen_from', 'action', 'screen_to', 'parent']

    def __init__(self, sf, action, st):
        self.screen_from = sf
        self.action = action
        self.screen_to = st
        self.parent = None

    def __eq__(self, other):
        return (self.screen_from, self.action, self.screen_to) == (
            other.screen_from, other.action, other.screen_to)

    def raw(self):
        return (self.screen_from, self.action, self.screen_to)

    def __str__(self):
        return str((self.screen_from, self.action, self.screen_to))


SCREEN_SWITCH_ACTIONS = (
    ('MESSAGES', 'MID_DOWN', 'CONTACTS'),
    ('MESSAGES', 'LEFT_UP', 'PROFILE_ENTRY'),

    ('CONTACTS', 'GROUPS', 'GROUP_LIST'),
    ('CONTACTS', 'LEFT_DOWN', 'MESSAGES'),

    ('GROUP_LIST', 'LEFT_UP', 'CONTACTS'),

    ('GROUP_CHAT', 'LEFT_UP', 'GROUP_LIST'),
    ('GROUP_CHAT', 'RIGHT_UP', 'GROUP_INFO'),

    ('GROUP_INFO', 'LEFT_UP', 'GROUP_CHAT'),

    ('PROFILE_ENTRY', 'QQ_NAME', 'PROFILE_CARD'),
    ('PROFILE_ENTRY', 'PROFILE_TO_MSG', 'MESSAGES'),

    ('PROFILE_CARD', 'LEFT_UP', 'PROFILE_ENTRY'),
)


def find_start_step(name):
    ret = []
    for ss in SCREEN_SWITCH_ACTIONS:
        if ss[0] == name:
            ret.append(SSA(*ss))
    return ret


def find_end_step(name):
    ret = []
    for ss in SCREEN_SWITCH_ACTIONS:
        if ss[2] == name:
            ret.append(SSA(*ss))
    return ret


def find_path(screen_from, screen_to):
    if screen_from == screen_to:
        return []

    open_list = find_start_step(screen_from)
    close_list = []
    last_node = None
    while True:
        #print_ssa_list(open_list)
        if len(open_list) == 0:
            break
        for node in open_list:
            if node.screen_to == screen_to:
                last_node = node
                break
        if last_node:
            break
        node = open_list.pop(0)
        if node not in close_list:
            close_list.append(node)
        neighbors = find_start_step(node.screen_to)
        for n in neighbors:
            if n in close_list or n in open_list:
                continue
            n.parent = node
            open_list.append(n)
    if last_node is None:
        #logger.error('No path from %s to %s', screen_from, screen_to)
        return None

    path = []
    while True:
        path.append(last_node.raw())
        if not last_node.parent:
            break
        last_node = last_node.parent
    return path[::-1]


def print_ssa_list(l):
    print [str(n) for n in l]


def test_find_path():
    print find_path('MESSAGES', 'CONTACTS')
    print find_path('GROUP_INFO', 'GROUP_LIST')
    print find_path('PROFILE_CARD', 'GROUP_LIST')
    print find_path('PROFILE_CARD', 'CONTACTS')
    print find_path('PROFILE_ENTRY', 'CONTACTS')

    print find_path('MESSAGES', 'GROUP_INFO')
    print find_path('CONTACTS', 'GROUP_CHAT')
    print find_path('PROFILE_CARD', 'GROUP_INFO')
    print find_path('PROFILE_CARD', 'GROUP_MEMBER')
    print find_path('CONTACTS', 'GROUP_MEMBER')


if __name__ == '__main__':
    test_find_path()
