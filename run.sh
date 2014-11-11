#!/bin/bash

. ./config.sh

function start_agent_check_group
{
    echo "start agent ..."
    monkeyrunner agent.py --qq ${qq} --device ${device} --test check_group
}

function start_agent_gen_group
{
    echo "start agent ..."
    monkeyrunner agent.py --qq ${qq} --device ${device} --test gen_group
}

function start_agent_test
{
    echo "start agent ..."
    monkeyrunner agent.py --qq ${qq} --device ${device} --test test
}

function start_robot
{
    echo "start robot ..."
    monkeyrunner robot.py --qq ${qq} --device ${device}
}

function back_up
{
    echo "back up env ..."
    cp ./grouplist/${qq}.grouplist ./grouplist/${qq}.grouplist.bak
}

function main
{
    model=${1:-agent}
    back_up
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
