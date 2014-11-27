#!/bin/bash

function check_robot_status
{
    log=$1
    grep "com.android.chimpchat.adb" ${log} > /dev/null 2>&1 && return 1
    grep "register robot succeed" ${log} >/dev/null 2>&1 && return 0
    return 2
}

function wait_robot
{
    for((i=0;i<20;i++))
    do
        check_robot_status
        ret=$?
        if [[ $ret == 0 ]];then
            return 0
        elif [[ $ret == 1 ]];then
            return 1
        fi
        sleep(3)
    done
    return 2
}

function start_robot
{
    echo "start robot ..."
	exist_job=`ps -elf | grep robot.py | grep $1 | awk '{print $4}'`
	if [[ $exist_job ]];then
		kill -9 $exist_job
	fi
	sleep 1
    for((i=0;i<5;i++))
	do
		nohup monkeyrunner robot.py --device $1 > screenlog/$1 2>&1 &
		ppid=$!
        wait_robot
        ret=$?
        if [[ $ret == 0 ]];then
            echo "start robot succeed!"
            return 0
        elif [[ $ret == 2 ]];then
            echo "start robot timeout! Retry..."
        else
            echo "start robot failed! Retry..."
        fi
        kill -9 $ppid
	done
    echo "failed to start robot 5 times, abort"
    return 1
}

function main
{
    device=${1:-5554}
    start_robot ${device}
}

main $@
