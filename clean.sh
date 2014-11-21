#!/bin/bash

function start_emulator
{
    for((i=1;i<=8;i++))
    do
        pid=$(ps -ef|grep emulator|grep "S${i}"|awk '{print $2}')
        kill -9 ${pid}
        sleep 2
        emulator -avd "S${i}" &
        sleep 2
    done
}

function reinstall_qq
{
    device=$1
    adb -s ${device} shell am force-stop com.tencent.mobileqq
    sleep 2
    adb -s ${device} uninstall com.tencent.mobileqq
    sleep 2
    adb -s ${device} install qq_apk/qq_v5.1.1.2245.apk
	sleep 2
	adb -s ${device} shell input keyevent 82
	adb -s ${device} shell input keyevent KEYCODE_HOME
	sleep 1
	adb -s ${device} shell am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity
	sleep 5
	adb -s ${device} shell input keyevent KEYCODE_BACK
}

function reinstall_all
{
    devices=$(adb devices|grep '^emulator'|awk '{print $1}')
	for device in ${devices}
	do
		reinstall_qq ${device} &
	done
	wait
}

reinstall_all
