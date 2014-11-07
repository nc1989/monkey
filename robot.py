#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
from threading import Thread
from optparse import OptionParser
from lib.agent import Agent
from lib.tools import url_get, url_post, get_local_ip
import logging
LOG_FORMAT = '%(asctime)s %(name)-5s %(levelname)-6s> %(message)s'
logging.basicConfig(datefmt='%m-%d %H:%M:%S', level=logging.DEBUG,
                    format=LOG_FORMAT, filename='agent.log',
                    encoding='utf8', filemode='w')
logger = logging.getLogger('Main')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt='%m-%d %H:%M:%S'))
logging.getLogger('Main').addHandler(console)

jython_lib = '/usr/local/Cellar/jython/2.5.3/libexec/Lib'
sys.path.append("%s/site-packages/simplejson-3.6.3-py2.5.egg" % jython_lib)
sys.path.append("%s/site-packages/bottle-0.12.7-py2.5.egg" % jython_lib)

#for test
sys.path.append('/Users/zhaoqifa/tools/jython2.5.3/Lib/site-packages/simplejson-3.6.5-py2.5.egg/')
sys.path.append('/Users/zhaoqifa/tools/jython2.5.3/Lib/site-packages/bottle-0.12.7-py2.5.egg/')

import simplejson as json
from bottle import Bottle, run, request, response, get, post


app = Bottle()
AGENT = None


def job():
    while True:
        time.sleep(10)
        logger.info("job running...")


@app.get('/inspect')
def inspect():
    data = AGENT.status()
    return json.dumps({"status": 0, "data": data})


@app.post('/net_command')
def net_command():
    data = request.forms
    cmd = data.get('cmd', None)
    if cmd and hasattr(AGENT, cmd):
        executer = getattr(AGENT, cmd)
        ret = executer(data)
    else:
        logger.error("command[%s] not found!", cmd)
        ret = -1, "command not found!" % cmd
    response.content_type = 'application/json'
    if isinstance(ret, int):
        r = {"status": ret}
    elif isinstance(ret, (list, dict)):
        r = ret
    elif isinstance(ret, tuple):
        r = {"status": ret[0], "err_msg": ret[1]}
    else:
        r = {"status": 1, "error_msg": "Unknow error!"}
    return json.dumps(r)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--qq", dest="qq")
    (options, args) = parser.parse_args()

    qqlist_file = "./qqlist/qqlist.json"
    if not os.path.isfile(qqlist_file):
        logger.error("qqlist file[%s] not exist!", qqlist_file)
        sys.exit(1)
    f = open(qqlist_file, "r")
    qqlist = json.loads(f.read().strip())
    f.close()

    qq = options.qq
    local_ip = qqlist["ip"]
    robot_server = qqlist["server"]
    config = qqlist[options.qq]
    port = config["port"]
    device_id = config["deviceid"]
    # 以上这几步不做异常检查了，如果配置有误直接退出
    command_url = "http://%s:%s/net_command" % (local_ip, port)

    global AGENT
    AGENT = Agent(qq, device_id)

    #启动后台job
    th = Thread(target=job)
    th.setDaemon(True)
    th.start()

    #注册
    #TODO

    #启动web
    run(app, host='0.0.0.0', port=port)
