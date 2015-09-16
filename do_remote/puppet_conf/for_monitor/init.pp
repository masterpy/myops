class for_monitor {
user {"for_monitor":
shell=>"/bin/bash",
home=>"/home/for_monitor",
ensure=>present,
managehome=>"ture",
}
file { "for_monitor_home":
owner => for_monitor,
group => for_monitor,
path => "/home/for_monitor",
ensure => directory
}
file { "for_monitor_home_ssh":
owner => for_monitor,
group => for_monitor,
path => "/home/for_monitor/.ssh",
ensure => directory,
require=>File["for_monitor_home"]
}
file { "for_monitor_auth":
ensure => present,
owner => for_monitor,
group => for_monitor,
path => "/home/for_monitor/.ssh/authorized_keys",
source => "puppet:///modules/for_monitor/authorized_keys",
mode => 500,
require=>File["for_monitor_home_ssh"]
}
package {sudo: 
ensure=>present, 
} 
file {"default_sudo": 
owner=>"root", 
group=>"root", 
mode=>0440, 
source => "puppet:///modules/for_monitor/sudoers",
path => "/etc/sudoers",
require=>Package["sudo"], 
}
}
