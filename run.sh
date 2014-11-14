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
    monkeyrunner robot.py --device $1
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
