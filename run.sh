#!/bin/bash

function start_agent_check_group
{
    echo "start agent ..."
    monkeyrunner agent.py  --device $1 --test check_group
}

function start_agent_gen_group
{
    echo "start agent ..."
    monkeyrunner agent.py  --device $1 --test gen_group
}

function start_agent_test
{
    echo "start agent ..."
    monkeyrunner agent.py  --device $1 --test test
}

function start_robot
{
    echo "start robot ..."
	exist_job=`ps -elf | grep robot.py | grep $1 | awk '{print $4}'`
	if [[ $exist_job ]];then
		kill -9 $exist_job
	fi
	sleep 1
	while true
	do
		nohup monkeyrunner robot.py --device $1 > screenlog/$1 2>&1 &
		ppid=$!
		sleep 60
		grep "register robot succeed" screenlog/$1 >/dev/null 2>&1 && break
		echo "start robot failed! Retry..."
		kill -9 $ppid
	done
	echo "start robot succeed!"
}

function main
{
    device=${1:-5554}
    model=${2:-agent}
    if [[ ${model} == "robot" ]];then
        start_robot ${device}
    elif [[ ${model} == "check" ]];then
        start_agent_check_group ${device}
    elif [[ ${model} == "group" ]];then
        start_agent_gen_group ${device}
    else
        start_agent_test ${device}
    fi
}

main $@
