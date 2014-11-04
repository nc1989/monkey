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
    qqId = md.qq['qqId']
    print "------------ monkey_info for qq %s ------------" % qqId
    data = {
        'qq': qqId,
        'groupList': md.groupList,
        'currentGroup': md.currentGroup,
    }
    return json.dumps({"status": 0, "data": data})

@app.post('/net_command')
def net_command():
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
        if isinstance(ret, int):
            return json.dumps({'status': ret})
        else:
            return json.dumps({'status': 0, 'data': ret})

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--qq", dest="qq")
    (options, args) = parser.parse_args()

    qqlist_file = "./qqlist/qqlist.json"
    if not os.path.isfile(qqlist_file):
        print "Error : "
        sys.exit(1)
    f = open(qqlist_file,'r')
    qqlist = json.loads(f.read())
    f.close()

    qqlist[options.qq]['url'] = "http://%s:%s/net_command" % \
            (qqlist['ip'], qqlist[options.qq]['port'])
    # qqlist[options.qq]['robot_url'] = 'http://0.0.0.0:8017/net_command'
    qqlist[options.qq]['robot_url'] = 'http://192.168.217.191:8001/net_command'
    qqlist[options.qq]['grouplistfile'] = './grouplist/%s.grouplist' % options.qq   

    global md
    md = MonkeyDaemon(qqlist[options.qq])
    print '------------Now, Android QQ daemon is running for %s on url %s ----------' \
        % (md.qq['qqId'], md.qq['url'])
    th = Thread(target=start_listen, args=[ md.qq['port'] ])
    th.setDaemon(True)
    th.start()
    md.monkey_task_loop()
