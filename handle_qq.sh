#!/bin/bash

function stop_qq
{
    device=$1
	adb -s ${device} shell am force-stop com.tencent.mobileqq
	sleep 2
}

function start_qq
{
    device=$1
	adb -s ${device} shell input keyevent KEYCODE_MENU
	adb -s ${device} shell input keyevent KEYCODE_BACK
	adb -s ${device} shell am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity
	sleep 60
	adb -s ${device} shell input keyevent KEYCODE_BACK
	adb -s ${device} shell input keyevent KEYCODE_BACK
	adb -s ${device} shell input keyevent KEYCODE_BACK
	adb -s ${device} shell am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity
}

function handle_qq
{
	cmd=$1_qq
	deviceid=emulator-$2
	$cmd $deviceid &
	wait
}

function handle_all_qq
{
	cmd=$1_qq
    devices=$(adb devices|grep '^emulator'|awk '{print $1}')
	for device in ${devices}
	do
		$cmd ${device} &
	done
	wait
}

#handle_qq $@
handle_all_qq $1
