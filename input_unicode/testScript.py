#!-*- coding: utf-8 -*-
#!/bin/env python

import os, sys

deviceid = u'emulator-5556'
msg = u'aa 哈哈啊 bb'

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
import utils

#print("install 'Input Unicode' apk")
#utils.run_cmd("adb install -r %s"%
#        os.path.join(current_dir, "Input Unicode.apk"))
print("input raw 'unicode' characters")
utils.get_encoded_character(deviceid,msg)
print("Now, verify if encoded characters are in clipboard")

