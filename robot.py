# -*- coding: utf-8 -*-

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import time
from threading import Thread
from optparse import OptionParser
from lib.agent import Agent
from lib.tools import url_get, url_post, get_local_ip
import logging
LOG_FORMAT = '%(asctime)s %(name)-5s %(levelname)-6s> %(message)s'
#logging.basicConfig(datefmt='%m-%d %H:%M:%S', level=logging.DEBUG,
#                    format=LOG_FORMAT, filename='robot.log',
#                    encoding='utf8', filemode='w')
logger = logging.getLogger('Main')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt='%m-%d %H:%M:%S'))
logging.getLogger('Main').addHandler(console)

jython_lib = '/home/chris/jython2.5.3/Lib'
sys.path.append("%s/site-packages/simplejson-3.6.3-py2.5.egg" % jython_lib)
sys.path.append("%s/site-packages/bottle-0.12.7-py2.5.egg" % jython_lib)

#for test
sys.path.append('/Users/zhaoqifa/tools/jython2.5.3/Lib/site-packages/simplejson-3.6.5-py2.5.egg/')
sys.path.append('/Users/zhaoqifa/tools/jython2.5.3/Lib/site-packages/bottle-0.12.7-py2.5.egg/')

import simplejson as json
from bottle import Bottle, run, request, response, get, post


app = Bottle()
LISTNER = None


@app.get('/inspect')
def inspect():
    data = LISTNER.status()
    return json.dumps({"status": 0, "data": data})


@app.post('/net_command')
def net_command():
    data = request.forms
    cmd = data.get('cmd', None)
    if cmd and hasattr(LISTNER, cmd):
        executer = getattr(LISTNER, cmd)
        ret = executer(data)
    else:
        logger.error("command[%s] not found!", cmd)
        ret = -1, "command not found!" % cmd
    response.content_type = 'application/json'
    if isinstance(ret, int):
        #返回int表示状态码
        r = {"status": ret}
    elif isinstance(ret, (list, dict)):
        #返回list或者dict，表示成功，list和dict是返回的data
        r = {"status": 0, "data": ret}
    elif isinstance(ret, tuple):
        #返回tuple表示状态码和错误信息
        r = {"status": ret[0], "err_msg": ret[1]}
    else:
        r = {"status": 1, "error_msg": "Unknow error!"}
    return json.dumps(r)


class Robot(object):
    def __init__(self, qq, device):
        self.qq = qq
        config = self.load_config()
        self.local_ip = config["ip"]
        self.robot_server = config["server"]
        self.nickname = config[qq]["nickname"]
        self.port = config[qq]["port"]
        self.device_id = device
        # 以上这几步不做异常检查了，如果配置有误直接退出
        #Step 1. 创建agent，用于操作模拟器
        logger.info("启动Agent")
        self.agent = Agent(qq, self.device_id)
        if not self.agent.self_check():
            sys.exit(1)

        #Step 2. 注册到server
        self.register()

        #Step 3. 启动后台job
        logger.info("启动后台job任务")
        th = Thread(target=self.job)
        th.setDaemon(True)
        th.start()

    def job(self):
        while True:
            time.sleep(30)
            logger.info("job running...")

    def load_config(self):
        qqlist_file = "./qqlist/qqlist.json"
        if not os.path.isfile(qqlist_file):
            logger.error("qqlist file[%s] not exist!", qqlist_file)
            sys.exit(1)
        f = open(qqlist_file, "r")
        qqlist = json.loads(f.read().strip())
        f.close()
        return qqlist

    def register(self):
        logger.info("register robot to: %s", self.robot_server)
        command_url = "http://%s:%s/net_command" % (self.local_ip, self.port)
        groups = [{'groupId': gid, 'groupName': g.name}
                  for gid, g in self.agent.groups.iteritems()]
        data = {
            'cmd': 'register',
            'qq': self.qq,
            'qqName': self.nickname,
            'url': command_url,
            'groupList': json.dumps(groups)
        }
        server_url = "http://%s:8001/net_command" % self.robot_server
        ret = json.loads(url_post(server_url, data))
        if 'status' in ret and ret['status'] == 0:
            logger.info("register robot succeed!")
        else:
            logger.warning("register robot failed!")


    # 以下是暴露给net_command的API
    def enter_group(self, data):
        gid = data.get('group', None)
        if not gid:
            return -1, "group not found"
        return self.agent.enter_group(gid)

    def send_group_msg(self, data):
        group = data.get('group', None)
        msg = data.get('msg', None)
        if not (group and msg):
            return -1, "group or msg is None"
        return self.agent.send_group_msg(msg)

    def check_group_msg(self, data):
        msg = data.get('msg', None)
        if not msg:
            return -1, "msg is None"
        return self.agent.check_group_msg(msg)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--qq", dest="qq")
    parser.add_option("--device", dest="device")
    (options, args) = parser.parse_args()
    qq = options.qq
    device = options.device

    global LISTNER
    LISTNER = Robot(qq, device)
    run(app, host='0.0.0.0', port=LISTNER.port)
