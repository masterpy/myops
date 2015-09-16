class online_all {

user {"gaozezhou":
shell=>"/bin/bash",
home=>"/home/gaozezhou",
ensure=>present,
managehome=>"true", 
password=>'$1$5Ia5r0$DEsr5xq.KtqU3c2M6lsSG.'
}


user {"wangshuai":
shell=>"/bin/bash",
home=>"/home/wangshuai",
ensure=>present,
managehome=>"true",
password=>'$1$iCKzE$T8Tiwz9eDY1nIjqSF44QA1'
}

user {"dongyuntao":
shell=>"/bin/bash",
home=>"/home/dongyuntao",
ensure=>present,
managehome=>"true",
password=>'$1$/XLzE$JGmcE8bY7ewYG2jeCEaJm1'
}

user {"zhangchengshan":
shell=>"/bin/bash",
home=>"/home/zhangchengshan",
ensure=>present,
managehome=>"true",
password=>'$1$WlVzU1$npy0eBsMln3GbC5l8cESc1'
}

user {"wangwei":
shell=>"/bin/bash",
home=>"/home/wangwei",
ensure=>present,
managehome=>"true",
password=>'$1$cxpx$v1Fs/oZzH9/JQmVojnpsE1'
}


user {"for_monitor":
shell=>"/bin/bash",
home=>"/home/for_monitor",
ensure=>present,
managehome=>"true",
}

user {"for_ct":
shell=>"/bin/bash",
home=>"/home/for_ct",
ensure=>present,
managehome=>"true",
}

file { "for_ct_home_ssh":
owner => for_ct,
group => for_ct,
path => "/home/for_ct/.ssh",
ensure => directory,
require=>File["for_ct_home"]
}

file { "for_ct_auth":
ensure => present,
owner => for_ct,
group => for_ct,
path => "/home/for_ct/.ssh/authorized_keys",
source => "puppet:///modules/online_ct/authorized_keys",
mode => 500,
require=>File["for_ct_home_ssh"]
}

file { "etc_bashrc":
ensure => present,
owner => root,
group => root,
path => "/etc/bashrc",
source => "puppet:///modules/online_user/etc_bashrc",
mode => 644,
}

user {"biztech":
shell=>"/bin/bash",
home=>"/home/biztech",
ensure=>present,
managehome=>"true",
}

file { "biztech_home_ssh":
owner => biztech,
group => biztech,
path => "/home/biztech/.ssh",
ensure => directory,
mode => 755,
require=>File["biztech_home"]
}

file { "biztech_auth":
ensure => present,
owner => biztech,
group => biztech,
path => "/home/biztech/.ssh/authorized_keys",
source => "puppet:///modules/online_biztech/authorized_keys",
mode => 500,
require=>File["biztech_home_ssh"]
}

package {sudo: 
ensure=>latest, 
} 

file {"base_sudo": 
owner=>"root", 
group=>"root", 
mode=>0440, 
source => "puppet:///modules/online_all/base.sudoers",
path => "/etc/sudoers",
require=>Package["sudo"], 
}

}
