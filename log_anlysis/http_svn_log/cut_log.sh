#!/bin/bash
day_time = $("+%Y-%m-%d")
move_log_file()
{
    hour_time="01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 00"
    for i in $hour_time
    do
       mkdir -p /data/log_analysis/log_data/$date_time
       cd /data/log_analysis/$date_time
       $(awk "$4~/[0-9][0-9][/][A-Z][a-z][a-z][/][0-9]+[:]/$i" $1 > $i.log) 
    done
}
parse_log_file()
{
    hour_time="01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 00"
    log_dir="/data/log_analysis/log_data/$date_time"
    mkdir -p /data/log_analysis/script/
    cd /data/log_analysis/script/
    for i in $hour_time
       python log_analysis.py $i.log
}

move_log_file
parse_log_file
