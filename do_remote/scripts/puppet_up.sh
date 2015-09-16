#!/bin/bash
version=`rpm -qa | grep ^puppet-2.7`
if [ "$version" != 'puppet-2.7.25-1.el5' ];then
        service puppet stop
        rm -rf /var/lib/puppet/ssl/
        wget http://10.134.33.223/puppet_installnew.tar.gz
        tar -zxvf puppet_installnew.tar.gz
        cd puppet_install
        yum -y install libselinux libselinux-utils libselinux-devel libselinux-python libselinux-ruby libselinux-utils augeas-libs ruby-libs ruby ruby-augeas ruby-shadow facter
        rpm -Uvh puppet-2.7.25-1.el5.noarch.rpm
        rpm -Uvh ruby-1.8.7.374-2.el5.x86_64.rpm rubygem-ffi-1.0.9-11.el5.x86_64.rpm rubygem-net-ldap-0.2.2-4.el5.noarch.rpm rubygem-net-ping-1.5.3-4.el5.noarch.rpm rubygems-1.3.7-1.el5.noarch.rpm rubygem-stomp-1.2.10-1.el5.noarch.rpm ruby-irb-1.8.7.374-2.el5.x86_64.rpm ruby-libs-1.8.7.374-2.el5.x86_64.rpm ruby-rdoc-1.8.7.374-2.el5.x86_64.rpm --force --nodeps
        rpm -Uvh libffi-3.0.5-2.el5.x86_64.rpm

        rpm -Uvh mcollective-2.5.0-1.el5.noarch.rpm mcollective-common-2.5.0-1.el5.noarch.rpm mcollective-facter-facts-1.0.0-1.noarch.rpm mcollective-filemgr-agent-1.0.1-1.noarch.rpm mcollective-filemgr-client-1.0.1-1.noarch.rpm mcollective-filemgr-common-1.0.1-1.noarch.rpm mcollective-iptables-agent-3.0.1-1.noarch.rpm mcollective-iptables-client-3.0.1-1.noarch.rpm mcollective-iptables-common-3.0.1-1.noarch.rpm mcollective-logstash-audit-2.0.0-1.noarch.rpm mcollective-nettest-agent-3.0.3-1.noarch.rpm mcollective-nettest-client-3.0.3-1.noarch.rpm mcollective-nettest-common-3.0.3-1.noarch.rpm mcollective-nrpe-agent-3.0.2-1.noarch.rpm mcollective-nrpe-client-3.0.2-1.noarch.rpm mcollective-nrpe-common-3.0.2-1.noarch.rpm mcollective-package-agent-4.3.0-1.el5.noarch.rpm mcollective-package-client-4.3.0-1.el5.noarch.rpm mcollective-package-common-4.3.0-1.el5.noarch.rpm mcollective-puppet-agent-1.7.2-1.el5.noarch.rpm mcollective-puppet-client-1.7.2-1.el5.noarch.rpm mcollective-puppet-common-1.7.2-1.el5.noarch.rpm mcollective-service-agent-3.1.2-1.noarch.rpm mcollective-service-client-3.1.2-1.noarch.rpm mcollective-service-common-3.1.2-1.noarch.rpm mcollective-sysctl-data-2.0.0-1.noarch.rpm

        sed -i '/puppet.server.com/d' /etc/hosts
        echo "10.144.224.86  puppetca.server.com ">>/etc/hosts
        echo "10.144.224.82 puppet.server.com ">>/etc/hosts
        rm -f /etc/puppet/puppet.conf
        rm -f /etc/mcollective/server.cfg
        wget http://10.134.33.223/puppet.conf
        wget http://10.134.33.223/server.cfg
        sleep 3
        facter  | awk -F'=>' '{print $1":"$2}' >> /etc/mcollective/facts.yaml
        mv puppet.conf /etc/puppet/puppet.conf
        mv server.cfg /etc/mcollective/server.cfg
        puppet agent --test
        service mcollective restart
        chkconfig  mcollective on
fi
