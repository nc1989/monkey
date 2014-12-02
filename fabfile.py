# -*- coding:utf-8 -*-

import time

from fabric.api import run, local, roles, env, cd
env.hosts=[
    '10.128.38.132',
    '10.128.39.83', '10.128.39.55', '10.128.38.199', '10.128.39.51',
    '10.128.39.82',
    '10.128.39.21', '10.128.39.44', '10.128.39.45', '10.128.39.48',
    '10.128.39.46', '10.128.39.49', '10.128.39.75', '10.128.39.76',
    '10.128.39.77', '10.128.39.63'
]
env.user="chris"
env.password="12qwaszx"
env.port=22
#env.parallel=True
#env.skip_bad_hosts=True
#env.timeout=1
#env.warn_only=True

def ls():
    local('touch 123.log')

def pull():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('git pull')
        run('pkill adb')
        run('adb devices')

def clean():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash clean.sh')

def stop_qqs():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash handle_qq.sh stop')

def start_qqs():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash handle_qq.sh start')

def stop_robots():
    with cd('/home/chris/workspace/monkey-daemon'):
        run("ps -ef | grep robot | grep -v grep | awk '{print $2}' | xargs kill")

def start_robot(device):
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash run.sh %s && sleep 1' % device)

def start_robots():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash run.sh all && sleep 1')

def restartQQ(device):
    with cd('/home/chris/workspace/monkey-daemon'):
        run('adb -s %s shell am force-stop com.tencent.mobileqq && sleep 1' % device)
        time.sleep(3)
        run('adb -s %s shell am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity && sleep 1' % device)
        time.sleep(3)
