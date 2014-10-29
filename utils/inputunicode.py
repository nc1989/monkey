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
    start_app = "adb " + "-s " + deviceid + " shell am start -an com.symbio.input.unicode/.Main"
    click_dpad_down = "adb " + "-s " + deviceid + " shell input keyevent KEYCODE_DPAD_DOWN"
    click_dpad_enter = "adb " + "-s " + deviceid + " shell input keyevent KEYCODE_ENTER"
    click_dpad_space = "adb " + "-s " + deviceid + " shell input keyevent KEYCODE_SPACE"
    # log("%r"%text)
    run_cmd(start_app)
    time.sleep(1)
    text_list = text.split()
    log(text_list)
    text_list = [x.encode('utf8') if is_pure_alnum(x) else x for x in text_list]
    log(text_list)
    for t in text_list[:-1]:
        cmd = "adb -s %s shell input text %r"  % (deviceid, t.encode('unicode-escape'))
        run_cmd(cmd)
        run_cmd(click_dpad_space)
    cmd = "adb -s %s shell input text %r"  % (deviceid, text_list[-1].encode('unicode-escape'))
    run_cmd(cmd)

    run_cmd(click_dpad_down)
    if __DEBUG__:
        run_cmd(click_dpad_down)
    run_cmd(click_dpad_enter)
    # print("Done")


if __name__ == '__main__':
    get_encoded_character(deviceid, msg);