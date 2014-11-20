#!-*- coding: utf-8 -*-
#!/bin/env python

import os, sys

deviceid = u'emulator-5554'
#msg=u'http://s.dianping.com/event/37317?utm_source=co_diaochan&utm_medium=dp_qqpa&utm_term=group_gz&utm_content=event37317_141117 中了带基友去~'
msg=u'http://s.dianping.com/event/37317?utm_source=co_diaochan&utm_medium=dp_qqpa&utm_term=group_gz&utm_content=event37317_141117 asda'

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
import utils

#print("install 'Input Unicode' apk")
#utils.run_cmd("adb install -r %s"%
#        os.path.join(current_dir, "Input Unicode.apk"))
utils.get_encoded_character(deviceid,msg)

