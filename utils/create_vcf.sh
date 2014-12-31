#!/bin/bash

function create_vcf
{
    file=$1
    begin=$2
    end=$3
    while read line
    do
        echo "BEGIN:VCARD"
        echo "VERSION:3.0"
        echo "N:$line;;;;"
        echo "TEL;TYPE=cell:$line"
        echo "END:VCARD"
    done <<< "$(sed -n "${begin},${end}p" $file)"
}

function import_contacts
{
    index=$1
    lines=100
    for((i=0;i<$2;i++))
    do
        emu_index=$((5554+2*$i))
        echo $(($index+$i*$lines)) $(($index+$i*$lines+$lines-1)) 
        rm -f contacts.vcf
        create_vcf tel $(($index+$i*$lines)) $(($index+$i*$lines+$lines-1)) >> contacts.vcf
        adb -s emulator-"$emu_index" push contacts.vcf /sdcard/contacts.vcf
    done
}
function main
{
    main_index=$1
    import_contacts $main_index 5
}

main $@
