#!/bin/bash

function start_qq
{
    device=$1
	adb -s ${device} shell am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity
	sleep 5
	#adb -s ${device} shell input keyevent KEYCODE_BACK
}

function start_all_qq
{
    devices=$(adb devices|grep '^emulator'|awk '{print $1}')
	for device in ${devices}
	do
		start_qq ${device} &
	done
	wait
}

start_all_qq
