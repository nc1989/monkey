#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from time import sleep
from threading import Thread
from optparse import OptionParser

# jython_lib = '/usr/local/Cellar/jython/2.5.3/libexec/Lib'
jython_lib = '/home/chris/jython2.5.3/Lib'
sys.path.append("%s/site-packages/simplejson-3.6.3-py2.5.egg" % jython_lib)
import simplejson as json

sys.path.append("%s/site-packages/bottle-0.12.7-py2.5.egg" % jython_lib)
from bottle import Bottle, run, request, response, get, post

from lib.monkeyDaemon import MonkeyDaemon
from lib.tools import url_get, url_post, get_local_ip

app = Bottle()

def start_listen(port):
    u""" 线程入口，启动bottle开始监听 """
    run(app, host='0.0.0.0', port=int(port))

@app.get('/daemon_info')
def monkey_info():
    print "------------ monkey_info for qq %s %s ------------" % \
         (md.qq['qqName'],md.qq['qqId'])
    data = {
        'qq': md.qq,
        'groupList': md.groupList,
        'currentGroup': md.currentGroup,
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
    if hasattr(md, data['cmd']):
        print 'Info : dispatch cmd to net_command : ', data['cmd']
        executer = getattr(md, data['cmd'])
        ret = executer(data)
        if ret == -1:
            return json.dumps({'status': 1, 'data': ret})
        else:
            return json.dumps({'status': 0, 'data': ret})


# monkeyrunner run_android_qq.py --qq 3040493963
# monkeyrunner run_android_qq.py --qq 3067487368
# monkeyrunner run_android_qq.py --qq 2902424837
# monkeyrunner run_android_qq.py --qq 2195356784
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--qq",    dest="qq")
    (options, args) = parser.parse_args()

    # robot_url = 'http://0.0.0.0:8017/net_command'
    robot_url = 'http://192.168.217.191:8001/net_command'

    localIp = get_local_ip()
    qqs = {
        '2902424837': {
            'qqId':'2902424837',
            'qqName':'',
            'ip':localIp,
            'port':'8001',
            'deviceid':'emulator-5554',
            'robot_url':robot_url,
        },
        '2195356784': {
            'qqId':'2195356784',
            'qqName':'',
            'ip':localIp,
            'port':'8002',
            'deviceid':'emulator-5556',
            'robot_url':robot_url,
        },
        '3040493963': {
            'qqId':'3040493963',
            'qqName':'',
            'ip':localIp,
            'port':'8003',
            'deviceid':'emulator-5558',
            'robot_url':robot_url,
        },
        '3067487368': {
            'qqId':'3067487368',
            'qqName':'',
            'ip':localIp,
            'port':'8004',
            'deviceid':'emulator-5560',
            'robot_url':robot_url,
        },
    }

    # os.system('emulator -avd %s ' % emulator[options.qq])

    global md
    md = MonkeyDaemon(qqs[options.qq])
    print '------------Now, Android QQ daemon is running for %s %s on url %s ----------' \
            % (md.qq['qqName'].decode('utf8'), md.qq['qqId'], md.qq['url'])

    th = Thread(target=start_listen, args=[ md.qq['port'] ])
    th.setDaemon(True)
    th.start()

    md.monkey_task_loop()