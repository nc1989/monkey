## monkey-daemon
Android QQ的后台daemon程序,提供针对QQ的基本的底层API.

## user guide
- jython 2.5.3+ (推荐使用2.5.3即可)
- jython modules: bottle, simplejson
- Monkeyrunner使用的模块:
	MonkeyRunner, MonkeyDevice, EasyMonkeyDevice, By
	HierarchyViewer
- Android Studio (Beta v0.8.6+) 或者 Eclipse Android adt
- Input Unicode: 使用adb输入中文
	https://github.com/bingwei/inputchineseviaadb

## APIs

1, enter_group
# 进入指定的QQ群
# params:
	{
		'cmd': 'enter_group',
		'group': '1234567'
	}
# return:
	{
		"status": 0,
		"data": 0,
	}
	or
	{
		"status": 1,
		"data": -1,
	}

2, get_msgs
# 获取新的群消息
# params:
	{
		'cmd': 'get_msgs',
	}
# return:
	{
	    "data": [
	        {
	            "content": "有事没",
	            "nickname": "Don't ask me!",
	            "time": "12:35"
	        },
	        {
	            "content": "干嘛",
	            "nickname": "Don't ask me!",
	            "time": "12:36"
	        }
	    ],
	    "status": 0
	}


3, send_msg
# 发送群消息
# params:
	{
		'cmd': 'send_msg',
		'msg': 'msg content to send'
	}
# return
	{
	    "status": 0,
	    "data": 0,
	}
	or
	{
	    "status": 1,
	    "data": -1,
	}

