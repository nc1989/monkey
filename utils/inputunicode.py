# -*- coding: utf-8 -*-
#!/bin/env python

import subprocess as SP
import string
import time
import os
import sys

__DEBUG__ = 0

def log(msg):
    if __DEBUG__:
        print(msg)

def run_cmd(cmd, with_error = False):
    try:
        output, error = SP.Popen(cmd, stdout=SP.PIPE, stderr = SP.PIPE, shell = True).communicate()
        if with_error:
            return output.lower(), error.lower()
        return output.strip().lower() if not error else ""
    except ValueError, error:
        print("Error: %s occurs while running %s"%error, cmd)
    except OSError, err:
        print(err)

def is_pure_alnum(text):
    tmp_text = text.encode('utf8')
    # print(tmp_text)
    for i in tmp_text:
        if i.lower() not in \
            "".join([string.ascii_lowercase,\
                string.digits,string.punctuation]):
            # print("yes")
            return False
    return True


def get_encoded_character(deviceid,text):
    avd_device = "adb -s %s" % deviceid
    start_app = "%s shell am start -an com.symbio.input.unicode/.Main" % avd_device
    click_dpad_down = "%s shell input keyevent KEYCODE_DPAD_DOWN" % avd_device
    click_dpad_enter = "%s shell input keyevent KEYCODE_ENTER" % avd_device
    click_dpad_space = "%s shell input keyevent KEYCODE_SPACE" % avd_device
    # log("%r"%text)
    run_cmd(start_app)
    time.sleep(2)
    text_list = text.split()
    log(text_list)
    text_list = [x.encode('utf8') if is_pure_alnum(x) else x for x in text_list]
    log(text_list)
    for t in text_list[:-1]:
        cmd = "%s shell input text %r"  % (avd_device, t.encode('unicode-escape'))
        run_cmd(cmd)
        run_cmd(click_dpad_space)
    cmd = "%s shell input text %r"  % (avd_device, text_list[-1].encode('unicode-escape'))
    need_backslash = ['&', '*', '#', '(', ')', '>', '<', '|']
    for i in need_backslash:
        cmd = cmd.replace(i, '\\'+i)
    log(cmd)
    run_cmd(cmd)

    run_cmd(click_dpad_down)
    if __DEBUG__:
        run_cmd(click_dpad_down)
    run_cmd(click_dpad_enter)
    # print("Done")


if __name__ == '__main__':
    get_encoded_character(sys.argv[1], sys.argv[2]);
 #   get_encoded_character(deviceid, msg);


