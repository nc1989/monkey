#!/bin/bash

qq="2902424837"
device="emulator-5554"


function start_agent
{
    echo "start agent ..."
    monkeyrunner lib/agent.py --qq ${qq} --device ${device}
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
    else
        start_agent
    fi
}

main $@
