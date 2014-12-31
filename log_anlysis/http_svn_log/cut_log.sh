#!/bin/bash
##切割apache日志
##按照小时和日期切割
##Write by xjg2010go
##Date: 2014.12.31
##

day_time=$(date "+%Y-%m-%d")
mkdir -p /data/log_analysis/log_data/$day_time
log_dir="/data/log_analysis/log_data/$day_time"

mkdir -p /data/log_analysis/script/


move_log_file()
{
    mkdir -p /data/log_analysis/log_data/$day_time
    if [ "$1" == "" ]
    then
        echo "must input log file"
        exit
    fi
    awk -v b=$day_time 'BEGIN{m["Jan"]="01";m["Feb"]="02";m["Mar"]="03";m["Apr"]="04";m["May"]="05";m["Jun"]="06";m["Jul"]="07";m["Aug"]="08";m["Sep"]="09";m["Oct"]="10";m["Nov"]="11";m["Dec"]="12";dir=b}{split($4,str,"/");split(str[3],str_year_hour,":");year=str_year_hour[1];month=str[2];day=substr(str[1],2,2);hour=str_year_hour[2];str_format=sprintf("/data/log_analysis/log_data/%s/%s-%s-%s-%sH.log",dir,year,m[month],day,hour);print $0 >> str_format;}' $1
}

parse_log_file()
{
    cd /data/log_analysis/script/
    for i in $(ls $log_dir)
    do
       python  log_analysis.py $log_dir/$i
    done
}

move_log_file $1
parse_log_file
