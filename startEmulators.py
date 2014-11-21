# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys
import time

def restart_adb():
    os.system("adb kill-server")
    os.system("adb devices")
    time.sleep(5)

def restart_emulator(device):
    print ">>> device", device
    os.system("emulator -avd %s &" % device)
    time.sleep(20)

if __name__ == '__main__':
    print ">>> start the emulators..."
    for i in xrange(1,9):
        restart_emulator('S%s' % i)

