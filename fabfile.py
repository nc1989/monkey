# -*- coding:utf-8 -*-

import time

from fabric.api import run, local, roles, env, cd
env.hosts=[
    '10.128.38.132',
    '10.128.39.83', '10.128.39.55', '10.128.38.199', '10.128.39.74',
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


def clean():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash clean.sh')


def robot(device):
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash run.sh %s robot && sleep 1' % device)


def restartQQ(device):
    with cd('/home/chris/workspace/monkey-daemon'):
        run('adb -s %s shell am force-stop com.tencent.mobileqq && sleep 1' % device)
        time.sleep(3)
        run('adb -s %s shell am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity && sleep 1' % device)
        time.sleep(3)

