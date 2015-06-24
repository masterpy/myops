#!/bin/bash

#删除原网卡路由
function route_del()
{
	for dev in eth0 eth1
	do
		masks=`ip route  | grep "$dev " | awk '{print $1}'`
		for mask in $masks
		do
			ip route del $mask dev $dev
		done
	done
}

#激活vlan 虚拟网卡接口
function up_interface()
{
	vlan_stats_file="/var/lib/vlan/vlan_stats"
	$(cat vlan_stats_file) | while read line
	do
		echo line
	done
}

#检查vlan ip 的联通性
function check_network()
{
	vlan_ip=$1
	ping -c 3 $vlan_ip
	if [ $? -ne 0 ]
	then
		return 1   #网络不通
	else
		return 0   #网络通畅
    fi   
}

#检查vlan ip是否配置到网卡以及网卡是否激活
function check_interface()
{

}


#检查路由表
function check_route()
{

}

up_interface
