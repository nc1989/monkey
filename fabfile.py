# -*- coding:utf-8 -*-

import time

from fabric.api import run, local, roles, env, cd, hosts, put
env.hosts=[
    '10.128.39.2',
    '10.128.39.83', '10.128.38.55', '10.128.38.199', '10.128.39.51',
    '10.128.39.82',
    '10.128.39.21', '10.128.39.44', '10.128.39.45', '10.128.39.48',
    '10.128.39.46', '10.128.39.49', '10.128.39.70', '10.128.39.76',
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

@hosts('10.128.39.83', '10.128.39.55', '10.128.38.199', '10.128.39.51', '10.128.39.82', '10.128.39.2')
def install_wechat():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('adb -s emulator-5554 install qq_apk/weixin600android501.apk')
        run('adb -s emulator-5556 install qq_apk/weixin600android501.apk')
        run('adb -s emulator-5558 install qq_apk/weixin600android501.apk')
        run('adb -s emulator-5560 install qq_apk/weixin600android501.apk')
        run('adb -s emulator-5562 install qq_apk/weixin600android501.apk')

@hosts('10.128.39.83', '10.128.39.55', '10.128.38.199', '10.128.39.51', '10.128.39.82', '10.128.39.2')
def import_contacts():
    with cd('/home/chris/workspace/monkey-daemon'):
        put('tel', 'utils/tel')

def clean():
    with cd('/home/chris/workspace/monkey-daemon'):
        run('bash clean.sh')

