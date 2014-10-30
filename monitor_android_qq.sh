#!/bin/sh

qq="3067487368"
curtime=`date +%Y-%m-%d-%s`
logdir="./log/${qq}-${curtime}"
`mkdir -p ${logdir}`
logfile="${logdir}/${qq}.log"
errfile="${logdir}/${qq}.err"
`touch ${logfile}`
`touch ${errfile}`

start_android_qq()
{
	# md_pid=`pgrep -lf monkeyrunner | grep ${qq} | awk '{print $1}'`
	md_pid=`ps -ef | grep monkeyrunner | grep ${qq} | grep -v grep | awk '{print $2}'`

	if [ -z ${md_pid} ];then
	echo ">>> Info : start the android qq for ${qq} !"
	else
	kill ${md_pid}
	echo ">>> Info : kill the previous process ${md_pid} !"
	echo ">>> Info : restart the android qq for ${qq} !"
	fi

	echo ">>> Info : please wait about 40 seconds !"
	monkeyrunner run_android_qq.py --qq ${qq} 1>${logfile} 2>${errfile} &
	sleep 40
}

monitor_adb()
{
	adb_info=`adb devices`
	# echo ${adb_info}
}

main()
{
	err1="Error sending touch event"
	err2="java.net.SocketException: Broken pipe"
	err3="Script terminated due to an exception"
	err4="Error sending drag start event"
	err5="Exception in thread"
	echo ">>> Info : try to start android qq !" > ${logfile}
	echo ">>> Info : try to start android qq !" > ${errfile}
	start_qq_success=0
	start_android_qq
	while [ ${start_qq_success} -eq 0 ]
	do
		# grep "${err1}" ${errfile}
		grep -E "${err1}|${err2}|${err3}|${err4}|${err5}" ${errfile}
		if [ $? -eq 0 ];then
			echo "\n>>> Info : try again !"
		    start_android_qq
		else
			succ_info="Now, Android QQ daemon is running"
			grep "${succ_info}" ${logfile}
			if [ $? -eq 0 ];then
				start_qq_success=1
				break
			fi
		fi
	done

	if [ ${start_qq_success} -eq 1 ];then
		echo "\n>>> Info : monitor_adb !"
		while true
		do
			
			monitor_adb
		done
	fi
}

main $@
