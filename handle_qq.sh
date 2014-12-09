#!/bin/bash

function stop_qq
{
    deviceid=$1
	port=${deviceid:0-4:4}
	device='S'$[ ( port - 5552 ) / 2 ]
	echo $deviceid
	echo $device
	adb -s ${deviceid} shell am force-stop com.tencent.mobileqq
	sleep 5
	ps -ef | grep 'emulator' | grep -v grep | grep $device | awk '{print $2}' | xargs kill
}

function start_qq
{
    deviceid=$1
	port=${deviceid:0-4:4}
	device='S'$[ ( port - 5552 ) / 2 ]
	echo $deviceid
	echo $device
	#emulator -avd $device -port $port &
	export DISPLAY=":0.0"
	xterm -display $DISPLAY -e "emulator -avd $device -port $port" &
	sleep 60
	adb -s ${deviceid} shell input keyevent KEYCODE_HOME
	adb -s ${deviceid} shell input keyevent KEYCODE_MENU
	adb -s ${deviceid} shell input keyevent KEYCODE_BACK
	adb -s ${deviceid} shell am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity
	sleep 30
	adb -s ${deviceid} shell input keyevent KEYCODE_BACK
	adb -s ${deviceid} shell input keyevent KEYCODE_BACK
	adb -s ${deviceid} shell input keyevent KEYCODE_BACK
	adb -s ${deviceid} shell am start -n com.tencent.mobileqq/com.tencent.mobileqq.activity.SplashActivity
}

function handle_qqs
{
	cmd=$1_qq
	shift
	if [[ $# -eq 1 ]];then
		deviceid=emulator-$1
		echo $deviceid
		$cmd $deviceid &
	else
		deviceids=$@
#		devices=$(adb devices|grep '^emulator'|awk '{print $1}')
		for deviceid in $deviceids
		do
			echo $deviceid
			$cmd 'emulator-'$deviceid &
			sleep 10
		done
	fi
	wait
}

handle_qqs $@
