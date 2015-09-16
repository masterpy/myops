class bizop_sys {
file { "utilization":
owner => root,
group => root,
path => "/opt/BizopClient/utilization",
ensure => directory,
before => File["utilization.sh"]
}

file { "utilization_dir":
owner => root,
group => root,
path => "/opt/BizopClient",
ensure => directory,
before => File["utilization"]
}

file { "cron_utilization":
owner => root,
group => root,
path => "/etc/cron.d/utilization",
ensure => present,
source => "puppet:///modules/bizop_sys/utilization/cron_utilization"
}

file { "utilization.sh":
ensure => present,
mode => 644,
owner => root,
group => root,
path => "/opt/BizopClient/utilization/utilization.sh",
source => "puppet:///modules/bizop_sys/utilization/utilization.sh",
}

user {"odin":
shell=>"/bin/bash",
home=>"/home/odin",
ensure=>absent,
managehome=>"ture",
}
file { "odin_home":
path => "/home/odin",
ensure=>absent,
force => true
}

user {"netmonitor":
shell=>"/bin/bash",
home=>"/home/netmonitor",
ensure=>absent,
managehome=>"ture",
}
file { "netmonitor_home":
path => "/home/netmonitor",
ensure=>absent,
force => true
}

service { "psacct":
enable =>false,
ensure =>stopped,
}
service { "puppet":
enable =>false,
ensure =>stopped,
}
service { "ntpd":
enable =>false,
ensure =>stopped,
}
service { "snmpd":
enable =>true,
ensure =>running,
hasstatus => true,
hasrestart => true,
}
file { "snmpd_conf":
path => "/etc/snmp/snmpd.conf",
mode => 644,
owner=>"root", 
group=>"root",
source => "puppet:///modules/bizop_sys/snmp/snmpd.conf",
notify => Service["snmpd"],
}
file { "snmpd_options":
path => "/etc/sysconfig/snmpd.options",
mode => 755,
owner=>"root",
group=>"root",
source => "puppet:///modules/bizop_sys/snmp/snmpd.options",
notify => Service["snmpd"],
}
file { "snmpd_6":
path => "/etc/sysconfig/snmpd",
mode => 644,
owner=>"root",
group=>"root",
source => "puppet:///modules/bizop_sys/snmp/snmpd.options",
notify => Service["snmpd"],
}


file { "puppet_conf":
path => "/etc/puppet/puppet.conf",
mode => 644,
owner=>"root", 
group=>"root",
source => "puppet:///modules/bizop_sys/puppet.conf",
#notify => Service["puppet"],
}
file { "root_bashrc":
path => "/root/.bashrc",
mode => 644,
owner=>"root",
group=>"root",
source => "puppet:///modules/bizop_sys/bashrc",
}


file {"ntp-set.sh":
owner=>"root",
group=>"root",
mode=>0440,
source => "puppet:///modules/bizop_sys/ntp-set.sh",
path => "/root/ntp-set.sh",
}

exec {"bash /root/ntp-set.sh":
path => ["/usr/bin","/bin","/usr/sbin"],
subscribe => File["ntp-set.sh"],
refreshonly => true,
}
}
