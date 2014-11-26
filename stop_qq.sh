#!/bin/bash

function stop_qq
{
    device=$1
    adb -s ${device} shell am force-stop com.tencent.mobileqq
    sleep 2
}

function stop_all_qq
{
    devices=$(adb devices|grep '^emulator'|awk '{print $1}')
	for device in ${devices}
	do
		stop_qq ${device} &
	done
	wait
}

stop_all_qq
