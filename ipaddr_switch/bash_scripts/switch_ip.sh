#!/bin/bash

function modify_ip()
{
    SLEEP=$1
    HOSTNAME=$2
    ACTIVE_IP=$3
    ETH0=$4
    ETH1=$5

    INSTALL_DIR=/usr/local/switch/
    MODIFY_IP_SH=modify_ip.sh
    rm -f $MODIFY_IP_SH
    mkdir /usr/local/switch -p >>$MODIFY_IP_SH
#    echo "service network stop" >>$MODIFY_IP_SH
    echo "ifdown eth0"
    echo "sed -i.bak "s/IPADDR.*=.*/IPADDR="$ETH0"/g" /etc/sysconfig/network-scripts/ifcfg-eth0" >>$MODIFY_IP_SH
    echo "sed -i.bak "/HWADDR*/d" /etc/sysconfig/network-scripts/ifcfg-eth0" >>$MODIFY_IP_SH
    echo "eth0 => $ETH0"


    if [ -n "$ETH1" ] ;then
        echo "sed -i.bak "s/IPADDR.*=.*/IPADDR="$ETH1"/g" /etc/sysconfig/network-scripts/ifcfg-eth1" >>$MODIFY_IP_SH
        echo "sed -i.bak "/HWADDR*/d" /etc/sysconfig/network-scripts/ifcfg-eth1" >>$MODIFY_IP_SH
        echo "eth1 => $ETH1"
    fi

    if [ -n "$HOSTNAME" ] ;then
        echo "hostname $HOSTNAME" >>$MODIFY_IP_SH
    echo "sed -i '/HOSTNAME/d' /etc/sysconfig/network"  >>$MODIFY_IP_SH
    echo "echo 'HOSTNAME=${HOSTNAME}' >> /etc/sysconfig/network" >>$MODIFY_IP_SH
    fi

    echo "sleep $SLEEP" >>$MODIFY_IP_SH
    echo "service network start" >>$MODIFY_IP_SH

    #HOSTNAME=`grep "^$ETH0 " $HOSTNAME_FILE|cut -d" " -f2`
    #HOSTNAME=`awk -v eth0="$ETH0" '{if($1 == eth0)print $0;}' $HOSTNAME_FILE|cut -d" " -f2`
    echo "service syslog restart" >>$MODIFY_IP_SH

    #echo "rm -f $INSTALL_DIR$MODIFY_IP_SH" >>$MODIFY_IP_SH
    rsync -av $MODIFY_IP_SH $ACTIVE_IP:$INSTALL_DIR >/dev/null
    ssh $ACTIVE_IP "atd;at now -f $INSTALL_DIR$MODIFY_IP_SH"
    rm -f $MODIFY_IP_SH
    echo "IP切换完毕，请在 ${SLEEP} 秒后重新连接" |tee -a $LOGNAME
    return 0
}


    OPT=$1
    MHOSTNAME=`echo $2 | awk -F. '{print $1}'`
    SHOSTNAME=`echo $3 | awk -F. '{print $1}'`
    RUNNING_1=$4
    STANDBY_1=$5
    RUNNING_2=$6
    STANDBY_2=$7

    echo $MHOSTNAME,$SHOSTNAME,$RUNNING_1,$RUNNING_2,$STANDBY_1,$STANDBY_2 >> root

    if [ ${OPT} == "ms" ];then
            modify_ip 30 $SHOSTNAME $RUNNING_1 $STANDBY_1 $STANDBY_2
            modify_ip 5 $MHOSTNAME $STANDBY_1 $RUNNING_1 $RUNNING_2

    elif [ ${OPT} == "s" ] ;then
            modify_ip 5 $MHOSTNAME $STANDBY_1 $RUNNING_1 $RUNNING_2
    fi
