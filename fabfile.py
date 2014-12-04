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

def environment():
    run("echo cd /home/chris/workspace/monkey-daemon >> ~/.bash_profile")

def pull():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('git pull')

def clean():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash clean.sh')

def restart_adb():
    run('pkill adb')
    time.sleep(3)
    run('adb devices')
    time.sleep(10)

def start_emulator(device, deviceid):
    run('emulator -avd %s -port %s &' % (device, deviceid))
    time.sleep(10)
    run('adb -s %s shell input keyevent KEYCODE_MENU' % deviceid)

def stop_emulator(device, deviceid):
    run("ps -ef | grep emulator | grep %s | grep %s | grep -v grep | \
        awk '{print $2}' | xargs kill" % (device, deviceid))

def start_qq(deviceid):
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash handle_qq.sh start %s' % deviceid)

def stop_qq(deviceid):
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash handle_qq.sh stop %s' % deviceid)

def start_robot(deviceid):
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash run.sh %s && sleep 1' % deviceid)

def stop_robot(deviceid):
    run("ps -ef | grep robot | grep %s | grep -v grep | \
        awk '{print $2}' | xargs kill" % deviceid)

def start_robots():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash run.sh all && sleep 1')

def stop_robots():
    run("ps -ef | grep robot | grep -v grep | \
        awk '{print $2}' | xargs kill")

def restartQQ(deviceid):
    run('adb -s emulator-%s shell am force-stop \
            com.tencent.mobileqq && sleep 1' % deviceid)
    time.sleep(3)
    run('adb -s emulator-%s shell am start -n \
        com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity \
        && sleep 1' % deviceid)
    time.sleep(3)
