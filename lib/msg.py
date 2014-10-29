# -*- coding: utf-8 -*-
#!/usr/bin/python

class Msg(object):
    def __init__(self, content, nickname, drag):
        self.content = content
        self.nickname = nickname
        self.drag = drag

    def __eq__(self, other):
        return self.content == other.content and self.nickname == other.nickname

