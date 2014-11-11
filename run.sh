#!/bin/bash

function start_agent_check_group
{
    echo "start agent ..."
    monkeyrunner agent.py  --test check_group
}

function start_agent_gen_group
{
    echo "start agent ..."
    monkeyrunner agent.py  --test gen_group
}

function start_agent_test
{
    echo "start agent ..."
    monkeyrunner agent.py  --test test
}

function start_robot
{
    echo "start robot ..."
    monkeyrunner robot.py
}

function main
{
    model=${1:-agent}
    if [[ ${model} == "robot" ]];then
        start_robot
    elif [[ ${model} == "check" ]];then
        start_agent_check_group
    elif [[ ${model}} == "group" ]];then
        start_agent_gen_group
    else
        start_agent_test
    fi
}

main $@
