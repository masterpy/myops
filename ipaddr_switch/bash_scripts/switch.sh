#!/bin/bash

function modify_ip()
{
    SLEEP=$1
    HOSTNAME=$2
    MASTER_IP=$3
    SLAVE_IP_ETH0=$4
    SLAVE_IP_ETH1=$5
    LOGNAME="/tmp/switch.log"

    echo "正在切换 ${ACTIVE_IP} 上的IP..." |tee -a $LOGNAME
    INSTALL_DIR="/usr/local/switch/"
    MODIFY_IP_SH="modify_ip.sh"
    rm -f $MODIFY_IP_SH
    echo "mkdir /usr/local/switch -p" >>$MODIFY_IP_SH

    echo "sed -i.bak "s/IPADDR.*=.*/IPADDR="$SLAVE_IP_ETH0"/g" /etc/sysconfig/network-scripts/ifcfg-eth0" >>$MODIFY_IP_SH
    echo "sed -i.bak "/HWADDR*/d" /etc/sysconfig/network-scripts/ifcfg-eth0" >>$MODIFY_IP_SH

    if [ -n "$SLAVE_IP_ETH1" ] ;then
        echo "sed -i.bak "s/IPADDR.*=.*/IPADDR="$SLAVE_IP_ETH1"/g" /etc/sysconfig/network-scripts/ifcfg-eth1" >>$MODIFY_IP_SH
        echo "sed -i.bak "/HWADDR*/d" /etc/sysconfig/network-scripts/ifcfg-eth1" >>$MODIFY_IP_SH

    fi

    if [ -n "$HOSTNAME" ] ;then
        echo "hostname $HOSTNAME" >>$MODIFY_IP_SH
	    echo "sed -i '/HOSTNAME/d' /etc/sysconfig/network"  >>$MODIFY_IP_SH
	    echo "echo 'HOSTNAME=${HOSTNAME}' >> /etc/sysconfig/network" >>$MODIFY_IP_SH
    fi

    echo "service network stop" >>$MODIFY_IP_SH
    echo "sleep $SLEEP" >>$MODIFY_IP_SH
    echo "service network start" >>$MODIFY_IP_SH

    #HOSTNAME=`grep "^$ETH0 " $HOSTNAME_FILE|cut -d" " -f2`
    #HOSTNAME=`awk -v eth0="$ETH0" '{if($1 == eth0)print $0;}' $HOSTNAME_FILE|cut -d" " -f2`
    echo "service syslog restart" >>$MODIFY_IP_SH

    #echo "rm -f $INSTALL_DIR$MODIFY_IP_SH" >>$MODIFY_IP_SH
    rsync -av $MODIFY_IP_SH $MASTER_IP:$INSTALL_DIR >/dev/null
    ssh $MASTER_IP "atd;at now -f $INSTALL_DIR$MODIFY_IP_SH"
    echo "" > $MODIFY_IP_SH
    echo "IP切换完毕，请在 ${SLEEP} 秒后重新连接" |tee -a $LOGNAME
    return 0
}


    OPT=$1
    MHOSTNAME=`echo $2 | awk -F. '{print $1}'`
    SHOSTNAME=`echo $3 | awk -F. '{print $1}'`
    RUNNING_eth0=$4
    RUNNING_eth1=$5
    STANDBY_eth0=$6
    STANDBY_eth1=$7
    echo
#	echo $MHOSTNAME,$SHOSTNAME,$RUNNING_1,$STANDBY_1,$RUNNING_2,$STANDBY_2

	if [ ${OPT} == "ms" ];then
            echo "$SHOSTNAME $RUNNING_eth0 $STANDBY_eth0 $STANDBY_eth1"
        	modify_ip 20 $SHOSTNAME $RUNNING_eth0 $STANDBY_eth0 $STANDBY_eth1
            echo "$MHOSTNAME $STANDBY_eth0 $RUNNING_eth0 $RUNNING_eth1"
        	modify_ip 5  $MHOSTNAME $STANDBY_eth0 $RUNNING_eth0 $RUNNING_eth1

	elif [ ${OPT} == "s" ] ;then
        	modify_ip 5 $MHOSTNAME $STANDBY_eth0 $RUNNING_eth0 $RUNNING_eth1
	fi
