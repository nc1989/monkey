#!/bin/bash

qqlist=(
		2902424837
		2195356784
		3040493963
		3067487368
		2901490931
		3083207001
		252709415
		2741625079
		3047289506
		2971248806
)

fetch_qqlist()
{
	qq_file='./qqlist/qqlist.json'
	qqlist=( $(jq 'keys | del(.[] | select(. == "ip")) | .[]' ${qq_file}) )
	echo ${qqlist[@]}
}

monitor_adb()
{
	adb_info=`adb devices`
	echo ${adb_info}
	if [[ ${adb_info} =~ 'offline' ]];then
		echo ${adb_info}
		restart_adb
	fi
}

restart_adb()
{
	echo ">>> Info : restart adb server"
	adb kill-server
	adb devices
	sleep 5
}

restart_emulator()
{
	echo "\n>>>"
	emulator_pid=`ps -ef | grep emulator | grep $1 | grep -v grep | awk '{print $2}'`
	if [ -z ${emulator_pid} ];then
		echo ">>> Info : emulator $1 is not running, then start it"
	else
		echo ">>> Info : emulator $1 is running, then restart it"
		kill ${emulator_pid}
	fi
	emulator -avd $1 &
}

start_qq()
{
	for qq in ${qqlist[@]}
	do
		./monitor_android_qq.sh ${qq} &
	done
}

main()
{
	echo ">>> Info : check the devices status first !"
	restart_adb
	fetch_qqlist
	for qq in ${qqlist[@]}
	do
		device=`jq -r ".[${qq}].device" ${qq_file}`
		deviceid=`jq -r ".[${qq}].deviceid" ${qq_file}`
		if [ ${device} ];then
			restart_emulator ${device}
			sleep 30	
			echo ${device}		
		fi
	done
	echo ">>> Info : please wait about 3 minutes"
	sleep 300
	echo ">>> Info : monitor adb is running now ..."
	# while true
	# do
	# 	monitor_adb
	# 	sleep 60
	# done
}

main $@

