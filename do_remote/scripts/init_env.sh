###                   ###
###***  安装puppet ***###
###                   ###
function define_config()
{
    
    sed -i '/puppet.server.com/d' /etc/hosts
    sed -i '/puppetca.server.com/d' /etc/hosts
    echo "10.144.224.86  puppetca.server.com ">>/etc/hosts
    echo "10.144.224.82 puppet.server.com ">>/etc/hosts

    mv /etc/puppet/puppet.conf  /tmp/puppet.conf.BAK
    
    if [ -e "/etc/mcollective/server.cfg" ]
    then
        mv /etc/mcollective/server.cfg  /tmp/server.cfg.BAK
    fi

    rm -f /etc/mcollective/server.cfg  /tmp/server.cfg.BAK


    rsync -auv houston.repos.sogou-inc.com::SRC/conf/puppet/client/puppet.conf  /etc/puppet/puppet.conf
    rsync -auv houston.repos.sogou-inc.com::SRC/conf/puppet/mcollective/server.cfg  /etc/mcollective/server.cfg

    if [ -e "/etc/mcollective/facts.yaml" ]
    then
        if [ -e /tmp/facts.yaml.BAK ]
        then
            rm -f /tmp/facts.yaml.BAK
        fi
        mv /etc/mcollective/facts.yaml  /tmp/facts.yaml.BAK
    fi
    facter  | awk -F'=>' '{print $1":"$2}' >> /etc/mcollective/facts.yaml

    #step3 :同步配置
    rm -rf /var/lib/puppet/*
    puppet agent -t
    service mcollective restart
    chkconfig  mcollective on


}

###                                      ###
###***  安装python以及vlan ip部署工具 ***###
###                                      ###
function python_tool_install()
{
    mkdir -p /usr/local/tools/
#    rsync -auv houston.repos.sogou-inc.com::SRC/tools/vlan_client  /usr/local/tools/
    rsync -auv houston.repos.sogou-inc.com::SRC/soft/  /usr/local/src/

    version=$(rpm -qa |grep python-2.7.9-1)
    if [ $version == "python-2.7.9-1" ]
    then
        echo "already install python,exit!"
        exit
    fi
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
    tar zxf pip-6.0.6.tar.gz
    cd  pip-6.0.6
    /usr/local/python/bin/python setup.py install
    cd ..
    rm -rf pip-6.0.6.tar.gz
    rm -rf pip-6.0.6
}

###                                      ###
###***  判断操作系统版本              ***###
###                                      ###

function judge_sys_release()
{
    str_5_8=$(cat /etc/issue  | egrep "release 5.*")
    str_6_3=$(cat /etc/issue  | egrep "release 6.*")
    if [ "$str_5_8" != "" ]
    then
        install_rhel5_yum_repo
    fi

    if [ "$str_6_3" != "" ]
    then
        install_rhel6_yum_repo
    fi
}

###                                      ###
###***  安装周边  软件                ***###
###                                      ###
function yum_gerenal()
{
  yum  -y  install libselinux libselinux-utils libselinux-devel libselinux-python libselinux-ruby  libselinux-utils augeas-libs
  yum -y install openssl-devel readline-devel bzip2-devel sqlite-devel zlib-devel ncurses-devel db4-devel expat-devel
}

###                                      ###
###***  安装redhat5  软件             ***###
###                                      ###
function install_rhel5_yum_repo()
{
    yum  -y remove mcollective*
    yum -y remove puppet*
    mv /etc/yum.repos.d  /etc/yum.repos.d.BAK
    mkdir /etc/yum.repos.d
    rsync  houston.repos.sogou-inc.com::SRC/conf/yum_repo/sys_rhel5.repo  /etc/yum.repos.d/

    yum clean all
    yum -y install mcollective  puppet  facter  mcollective-puppet-agent mcollective-puppet-common
    python_tool_install

    rm -rf /etc/yum.repos.d
    mv /etc/yum.repos.d.BAK /etc/yum.repos.d
}

###                                      ###
###***  安装redhat6  软件             ***###
### 
function install_rhel6_yum_repo()
{
    yum remove mcollective* -y
    yum remove puppet* -y
    mv /etc/yum.repos.d  /etc/yum.repos.d.BAK
    mkdir /etc/yum.repos.d
    rsync  houston.repos.sogou-inc.com::SRC/conf/yum_repo/sys_rhel6.repo  /etc/yum.repos.d/

    yum clean all
    yum -y install mcollective  puppet  facter  mcollective-puppet-agent mcollective-puppet-common
    python_tool_install

    rm -rf /etc/yum.repos.d
    mv /etc/yum.repos.d.BAK /etc/yum.repos.d
}

###                                              ###
###***  验证执行结果                          ***###
###                                              ###

function check_result()
{
    mcollectived_pid=$(ps axu | grep mcollectived| grep -v "grep" | awk '{print $2}')
    user=$(cat /etc/passwd | grep "for_monitor" | cut -d ":" -f1)
    if [ "$mcollectived_pid" != "" -a "$user" != "" ]
    then
        echo 0
    else
        echo 1
    fi  
}

echo "10.139.45.69   houston.repos.sogou-inc.com" >> /etc/hosts
yum_gerenal
judge_sys_release
define_config
check_result
sed -i '/10.139.45.69/d' /etc/hosts

