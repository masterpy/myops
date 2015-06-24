#!/bin/bash

vlan_stats_file="/var/lib/vlan/vlan_stats"
#删除原网卡路由和rule 规则
function route_del()
{
    cat $vlan_stats_file | while read line
    do
        device=$(echo $line | egrep "^device_list" | cut -d ":" -f2)
        if [ "$device" == "" ]
        then
            continue
        else
            for dev in $device
            do
                masks=`ip route  | grep "$dev " | awk '{print $1}'`
                for mask in $masks
                do
                    #echo "ip route del $mask dev $dev"
                    ip route del $mask dev $dev
                done
            done
        fi       
    done

}

#删除vlan rule规则
function rule_del()
{
    cat $vlan_stats_file | while read line
    do
        priority_list=$(echo $line | egrep "^priority" | cut -d ":" -f2)
        if [ "$priority_list" == "" ]
        then
            continue
        else
            echo `echo $priority_list | cut -d " " -f1` > .priority_temp
            echo `echo $priority_list | cut -d " " -f2` > .priority_temp2
        fi
    done 
    priority1=`cat .priority_temp`
    priority2=`cat .priority_temp2`
    cat $vlan_stats_file | while read line
    do
        net_list=$(echo $line | egrep "^vlan_net_list" | cut -d ":" -f2)
        if [ "$net_list" == "" ]
        then
            continue
        else
            for net in $net_list
            do
                #echo "ip rule | grep $net | grep -v \"$priority1\"||\"$priority2\""
                str=`ip rule | grep $net | grep -v -e "$priority1" -e "$priority2"`
                for num in `echo $str | cut -d ":" -f1`
                do
                   #echo "ip rule del priority $num"
                   ip rule del priority $num
                done
            done
        fi
    done 
    rm -f ./.priority_temp
    rm -f ./.priority_temp2
}

function dots
{
    stty -echo >/dev/null 2>&1
    while true
    do  
        echo -e ".\c"
        sleep 1  
    done
    stty echo
}

#检查vlan ip是否配置到网卡以及网卡是否激活
function check_net()
{
    view=$1
    cat $vlan_stats_file | while read line
    do
        vdev=$(echo $line | grep "v_device_list" | cut -d ":" -f2)
        if [ "$vdev" != "" ]
        then
            echo `echo $vdev | cut -d " " -f1` > .result_temp
            echo `echo $vdev | cut -d " " -f2` > .result_temp2
        else
            continue 
        fi
    done
    
    dev1=`cat .result_temp`
    dev2=`cat .result_temp2`

    cat $vlan_stats_file | while read line
    do
        str1=`echo $line | grep "$dev1"|egrep -v "v_device_list|rt_table_list" | cut -d " " -f2`
        str2=`echo $line | grep "$dev2"|egrep -v "v_device_list|rt_table_list" | cut -d " " -f2`
        if [ "$str1" != "" ]
        then
            echo $str1 > .result_temp3
        elif [ "$str2" != "" ]
        then
            echo $str2 > .result_temp4
        else
            continue
        fi
    done
    ipaddr1=`cat .result_temp3`
    ipaddr2=`cat .result_temp4`


    for ip in $ipaddr1 $ipaddr2
    do
        /usr/bin/python /opt/opbin/tools/check_net.py -o check_network -n $ip
        #status=$(echo $ip_status | cut -d " " -f1 | cut -d "=" -f2)
        if [ "$?" == "0" ]
        then
            check_interface $ip
            if [ "$?" == "0" ]
            then
                continue
            else
                #表示网络通，网卡未激活，其他服务器已配置改 vlan ip
                return 1
            fi
        else
            rule_del
            route_del
            dev=$(cat /var/lib/vlan/vlan_stats  | grep $ip | cut -d ":" -f1)
            if [ "$view" != "" ]
            then
                trap 'kill $BG_PID;echo;exit' 1 2 3 15
                dots &
                BG_PID=$!
            fi
            #echo "ifup $dev"
            ifup $dev  > /dev/null  2>&1
            if [ "$view" != "" ]
            then
                kill $BG_PID
            fi 
            if [ "$?" == "0" ]
            then
                continue
            else
                #表示激活网卡失败
                return 2
            fi
        fi
    done
    rm -f ./.result_temp1
    rm -f ./.result_temp2
    rm -f ./.result_temp3
    rm -f ./.result_temp4
}

function check_interface()
{
    #
    #检查网络， 网卡已激活，返回0。
    #如果网络， 网卡未激活，返回1
    #
    ipaddr=$1
    /usr/bin/python /opt/opbin/tools/check_net.py -o check_interface -p $ipaddr

    if [ "$?" == "0" ]
    then
        return 0
    else
        return 1
    fi
}

#检查main路由表
function check_route()
{
    ip route | grep -v "scope link" > .temp_route
    str=""
    count=`ip route | grep -v "scope link" |wc -l`
    cat .temp_route | while read line 
    do
        /usr/bin/python /opt/opbin/tools/check_net.py -o check_route -s "$line" -c $count
        if [ "$?" == "0" ]
        then
            continue
        else
            return 1
        fi
    done   
}

#检查vlan ip网关
function check_vlan_gateway()
{
    for vip in $(cat /var/lib/vlan/vlan_stats  | grep "v_gateway" | cut -d ":" -f2)
    do
        /usr/bin/python /opt/opbin/tools/check_net.py -o check_network -n $vip
        if [ "$?" == "0" ]
        then
            continue
        else
            return 1
        fi
    done  
}

#启动函数(CS交互模式)
function start_daemon_ver()
{
    check_net
    if [ "$?" == "0" ]
    then
        rule_del
        route_del
        #0 表示网卡激活成功,vlan ip配置成功，路由已清理完毕
        #echo 0
    elif [ "$?" == "1" ]; then
        #1 表示网络通，网卡未激活，其他服务器已配置该vlan ip
        echo 1
        exit 1
    elif [ "$?" == "2" ]; then
        #2 表示激活网卡失败
        echo 2
        exit 2
    fi

    check_route
    if [ "$?" != "0" ]
    then
         #4表示路由表错误
        echo 3
        exit 3
    fi

    check_vlan_gateway
    if [ "$?" == "0" ]
    then
        #5 表示vlan ip网关可以ping通
        echo 5
    else
        #6 表示vlan ip网关不可以ping通
        echo 4
        exit 4
    fi
}

#启动函数(CC交互模式)
function start_daemon_no_ver()
{
    view="view"
    check_net $view
    if [ "$?" == "0" ]
    then
        echo
        echo "网卡激活.................成功"
    elif [ "$?" == "1" ]; then
        echo "vlan ip.................正在使用"
        exit 1
    elif [ "$?" == "2" ]; then
        echo "网卡激活.................失败"
        exit 2
    fi
    check_route
    if [ "$?" == "0" ]
    then
        echo "main路由表...................正确"
    else
        echo "main路由表...................错误"
        exit 4
    fi
    check_vlan_gateway
    if [ "$?" == "0" ]
    then
        echo "vlan ip网关...................畅通"
    else
        echo "vlan ip网关...................不通"
        exit 6
    fi
}

function stop_daemon()
{
    cat $vlan_stats_file | while read line
    do
        vdev=$(echo $line | grep "v_device_list" | cut -d ":" -f2)
        if [ "$vdev" != "" ]
        then
            for dev in $vdev
            do
                route_table=${dev}_table
                num=$(ip rule | grep $route_table| wc -l)
                while (( $num > 0 ))
                do
                    ip rule del table  $route_table
                    num=`expr $num - 1`
                done
                ifdown $dev > /dev/null  2>&1 
            done
        else
            continue 
        fi
    done
    /etc/init.d/network restart > /dev/null  2>&1 
    echo "The Vlan Network has been Deleted!"
}

function restart_dev()
{
    cat $vlan_stats_file | while read line
    do
        vdev=$(echo $line | grep "v_device_list" | cut -d ":" -f2)
        if [ "$vdev" != "" ]
        then
            for dev in $vdev
            do
                ifdown $dev 2>&1 
            done
        else
            continue 
        fi
    done

} 


function main()
{
    DESC="vlan ip network"
    NAME="vlan"
    case "$1" in
    start)
    echo -e "Starting $DESC"
    start_daemon_no_ver
    ;;
    stop)
    echo -e "Stopping $DESC\n"
    stop_daemon
    ;;
    csmode)
    start_daemon_ver
    ;;
    restart)
    echo -e "Restarting $DESC\n"
    restart_dev
    start_daemon_no_ver
    ;;
    *)
    echo -e "Usage: $SCRIPTNAME {start|stop|restart}\n" >&2
    exit 3
    ;;
    esac
    exit 0
} 

if [ -e "/var/lib/vlan/vlan_stats" ]
then
    action=$1 
    main $action
else
    echo 7
fi
