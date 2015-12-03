#!/bin/bash
#升级vlan ip新版本


rsync -auv 10.149.45.69::SRC/tools/vlan_client  /usr/local/tools/
rsync -auv 10.149.45.69::SRC/soft/  /usr/local/src/

if [ ! -d "/usr/local/python" ]
then
    cd  /usr/local/src/
    rpm -ivh python-2.7.9-1.x86_64.rpm
    rpm -ivh openssl-1.0.0s-1.x86_64.rpm
    ln -s /usr/local/openssl/lib/libcrypto.so.1.0.0 /usr/lib64/libcrypto.so.10 
    ln -s /usr/local/openssl/lib/libssl.so.1.0.0 /usr/lib64/libssl.so.10
    export LD_LIBRARY_PATH=/usr/lib64
    rm -f python-2.7.9-1.x86_64.rpm
    rm -f openssl-1.0.0s-1.x86_64.rpm
fi
    
sed -i '/vlan_client/d' /etc/profile
echo 'export PATH=/usr/local/tools/vlan_client/:$PATH' >> /etc/profile

source /etc/profile

cd /usr/local/src/
unzip setuptools-11.3.1.zip
cd setuptools-11.3.1
/usr/local/python/bin/python setup.py install
cd ..
rm -rf setuptools-11.3.1
rm -f setuptools-11.3.1.zip
tar zxf IPy-0.83.tar.gz
cd IPy-0.83
/usr/local/python/bin/python setup.py install
cd ..
rm -f IPy-0.83.tar.gz
rm -rf IPy-0.83
tar zxf netifaces-0.10.4.tar.gz
cd netifaces-0.10.4
/usr/local/python/bin/python setup.py install
cd ..
rm -rf netifaces-0.10.4
rm -f netifaces-0.10.4.tar.gz


echo "finsh python soft install"

cd /etc/sysconfig/network-scripts/

for filename in `ls /etc/sysconfig/network-scripts/`
do
    if [ "$filename" == "eth2.route" || "$filename" == "eth0.155.route" || "$filename" == "eth0.755.route" ]
    then
        mv $filename eth0.route
        gateway= `cat route-eth0 | cut -d " " -f3`
        sed -i  "s/GATEWAY0=.*/GATEWAY0=$gateway/g" eth0.route
        sed -i  "s/GATEWAY1=.*/GATEWAY1=$gateway/g" eth0.route
        if [ "$filename" == "eth0.155.route" ]
        then
            mv *.155  /tmp/
        elif [ "$filename" == "eth0.755.route" ]
            mv *.755 /tmp/
        else
            mv route-eth2  /tmp/
            mv rule-eth2   /tmp/       
        fi

    elif [ "$filename" == "eth3.route" || "$filename" == "eth1.255.route" || "$filename" == "eth1.855.route" ]
        mv $filename eth1.route
        gateway= `cat route-eth1 | cut -d " " -f3`
        sed -i  "s/GATEWAY0=.*/GATEWAY0=$gateway/g" eth1.route
        sed -i  "s/GATEWAY1=.*/GATEWAY1=$gateway/g" eth1.route
        sed -i  "s/GATEWAY1=.*/GATEWAY2=$gateway/g" eth1.route
        if [ "$filename" == "eth1.255.route" ]
        then
            mv *.255  /tmp/
        elif [ "$filename" == "eth1.855.route" ]
            mv *.855 /tmp/
        else
            mv route-eth3  /tmp/
            mv rule-eth3   /tmp/
        fi
done

data_ip_addr=""
bussi_ip_addr=""

for filename in `ls /etc/sysconfig/network-scripts/`
do
    if [ "$filename" == "ifcfg-eth2" || "$filename" == "ifcfg-eth0.155" || "$filename" == "ifcfg-eth0.755" ]
    then
        data_ip_addr=$(grep "IPADDR" $filename | cut -d "=" -f2)
    fi 

    if [ "$filename" == "ifcfg-eth3" || "$filename" == "ifcfg-eth1.255" || "$filename" == "ifcfg-eth1.855" ]
    then
        bussi_ip_addr=$(grep "IPADDR" $filename | cut -d "=" -f2)
    fi  

    if [  "$data_ip_addr" != "" && "$bussi_ip_addr" != "" ]
    then
        if [ "$filename" == "ifcfg-eth2" || "$filename" == "ifcfg-eth3" ]
        then
            /usr/local/python/bin/python /usr/local/tools/vlan_client/gerenate_route.py -b $bussi_ip_addr -d $data_ip_addr -o add -m 1
        elif [ "$filename" == "ifcfg-eth0.155" || "$filename" == "ifcfg-eth1.255" || "$filename" == "ifcfg-eth0.755" || "$filename" == "ifcfg-eth1.855" ]
        then
            /usr/local/python/bin/python /usr/local/tools/vlan_client/gerenate_route.py -b $bussi_ip_addr -d $data_ip_addr -o add -m 0
        fi
    fi

done


/etc/init.d/network restart
/usr/local/tools/vlan_client/scripts/vlan_start.sh  start





