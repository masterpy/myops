#!/bin/bash

function modify_ip()
{
    SLEEP=$1
    HOSTNAME=$2
    HOSTNAME_ALL=$6
    OLD_HOSTNAME=$7
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
	    echo "rm -rf /var/lib/puppet/ssl/" >>$MODIFY_IP_SH
	    echo "/bin/cp -rp /etc/hosts /tmp/hosts.BAK" >>$MODIFY_IP_SH
	    echo "sed -i '/$OLD_HOSTNAME/d' /etc/hosts" >>$MODIFY_IP_SH
            echo "echo \"$SLAVE_IP_ETH0  $HOSTNAME_ALL $HOSTNAME\" >> /etc/hosts">>$MODIFY_IP_SH
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
    rm -f $MODIFY_IP_SH
    echo "IP切换完毕，请在 ${SLEEP} 秒后重新连接" |tee -a $LOGNAME
    return 0
}

function reconnect_server()
{   
     INSTALL_DIR="/usr/local/switch/"
     PP_SH="puppet_connect.sh"
     MASTER_IP=$1
     echo  "puppet agent --server puppet.server.com  --test" >> $PP_SH
     rsync -av $PP_SH $MASTER_IP:$INSTALL_DIR >/dev/null
     ssh $MASTER_IP "atd;at now -f $INSTALL_DIR$PP_SH"
     echo "" > $PP_SH
     rm -f $PP_SH
}

function check_ip()
{
    if [ "$1" != "" -a "$2" != "" -a "$3" != "" -a "$4" != "" ]
    then
    Dangerous_ip="10.13.199.180 10.11.199.180 10.134.33.223 10.144.33.223"
    now_ip="$1 $2 $3 $4"
    for ip in $Dangerous_ip
    do
       for now_ip in $now_ip
       do
       echo $now_ip
            if [ "$now_ip" == "$ip" ]
            then
                 echo "$now_ip is Dangerous IP,Please Check it!"
                 exit
            fi
       done
    done
    else
        "There is a null args OR a null strings"
         exit
    fi
}

    OPT=$1
    MHOSTNAME=`echo $2 | awk -F. '{print $1}'`
    SHOSTNAME=`echo $3 | awk -F. '{print $1}'`
    MHOSTNAME_ALL=$2
    SHOSTNAME_ALL=$3
    RUNNING_eth0=$4
    RUNNING_eth1=$5
    STANDBY_eth0=$6
    STANDBY_eth1=$7
    echo
#	echo $MHOSTNAME,$SHOSTNAME,$RUNNING_1,$STANDBY_1,$RUNNING_2,$STANDBY_2

    check_ip  $RUNNING_eth0 $RUNNING_eth1 $STANDBY_eth0 $STANDBY_eth1
	
        if [ ${OPT} == "ms" ];then
            echo "$SHOSTNAME $RUNNING_eth0 $STANDBY_eth0 $STANDBY_eth1"
		ssh 10.134.33.223 "puppet cert -c $SHOSTNAME_ALL"
        	modify_ip 20 $SHOSTNAME $RUNNING_eth0 $STANDBY_eth0 $STANDBY_eth1 $SHOSTNAME_ALL $MHOSTNAME_ALL
		reconnect_server $STANDBY_eth0
            echo "$MHOSTNAME $STANDBY_eth0 $RUNNING_eth0 $RUNNING_eth1"
		ssh 10.134.33.223 "puppet cert -c $MHOSTNAME_ALL"
        	modify_ip 5  $MHOSTNAME $STANDBY_eth0 $RUNNING_eth0 $RUNNING_eth1 $MHOSTNAME_ALL $SHOSTNAME_ALL
		reconnect_server $RUNNING_eth0

	elif [ ${OPT} == "s" ] ;then
		ssh 10.134.33.223 "puppet cert -c $MHOSTNAME_ALL"
        	modify_ip 5 $MHOSTNAME $STANDBY_eth0 $RUNNING_eth0 $RUNNING_eth1 $MHOSTNAME_ALL $SHOSTNAME_ALL
                reconnect_server $RUNNING_eth0
	fi
