#!/bin/sh

curtime=`date +%Y-%m-%d-%s`
logdir="./log/${curtime}"
`mkdir -p ${logdir}`
qq="3067487368"
logfile="${logdir}/${qq}.log"
errfile="${logdir}/${qq}.err"
`touch ${logfile}`
`touch ${errfile}`

start_android_qq()
{
	md_pid=`pgrep -lf monkeyrunner | grep ${qq} | awk '{print $1}'`

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
	#err2="java.net.SocketException: Broken pipe"
	#grep -E "${err1}|${err2}" $errfile
	echo ">>> Info : try to start android qq !" > ${logfile}
	echo ">>> Info : try to start android qq !" > ${errfile}
	start_qq_success=0
	start_android_qq
	while [ ${start_qq_success} -eq 0 ]
	do
		grep "${err1}" ${errfile}
		if [ $? -eq 0 ];then
			echo "\n>>> Info : try again !"
		    start_android_qq
		else
			start_qq_success=1
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
