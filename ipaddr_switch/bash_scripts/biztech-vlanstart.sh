#!/bin/bash

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

dir="/etc/sysconfig/network-scripts"  #网卡配置所在目录
local_ip=`ifconfig  | grep 'inet addr' | awk -Faddr: '{print $2}' | awk '{print $1}'  | xargs`  #获取本机已使用的IP
local_net=`cd ${dir};ls | grep ^ifcfg-eth | egrep -v "lo|usb"` #获取本机网络设备配置文件
net_num=`cd ${dir};ls | grep ^ifcfg-eth | egrep -v "lo|usb"| wc -l` #获取本机网络设备数量

local_default=`ifconfig eth0 | grep Bcast | awk -FBcast: '{print $2}' | awk '{print $1}' | awk -F. '{print $1"."$2"."$3"."($4-1)}'` #获取本机eth0网关地址

default_num=`route | grep default | wc -l` #获取默认路由条数
if [ ${default_num} = "0" ];then  #如果配置默认路由，增加默认路由,防止VLANIP无法进行PING测试。
	route add default gw ${local_default}
fi
flag_route="0"
flag_route1="0"
for net in $local_net   #对本机网络设备上配置的IP与已使用IP地址进行比对
do
	flag="0"
	tmp_ip=`cat ${dir}"/"${net} | grep IPADDR | awk  -F= '{print $2}'`
	for ip in $local_ip
	do
		if [ "${tmp_ip}" = "${ip}" ];then
			flag="1"
			ifup $net
		fi
	done
	if [ ${flag} = "0" ];then #未启动的网络设备，检查IP能否ping通，不通则启用此设备
		tmp_device=`cat ${dir}"/"${net} | grep DEVICE | awk  -F= '{print $2}'`
		flag_route1="1"
		ping -c 2 $tmp_ip
		if [ "$?" != "0" ];then
			ifup $tmp_device
			flag_route="1"
		fi
	fi
done
if [ "$flag_route" = "1" ];then #新启用设备，删除实际IP路由。
	route_del
elif [ ${net_num} > 3 -a "${flag_route1}" = "0" ];then #VLANIP已绑定在本机，并且不是通过此次脚本中启用的，删除实际IP路由。
	route_del
fi
if [ ${default_num} = "0" ];then
	ip r del default
fi
