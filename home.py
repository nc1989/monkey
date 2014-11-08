#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


devices = ['5554','5556','5558',
	       '5560','5562','5564','5566','5568',
	 	   '5570','5572','5574','5576']
for dev in devices:
	cmd = "adb -s emulator-%s shell input keyevent KEYCODE_HOME" % dev
	print cmd
	os.system(cmd)
