class online_all {

user {"lizhi":
shell=>"/bin/bash",
home=>"/home/lizhi",
ensure=>present,
managehome=>"true",
password=>'$1$kEiQt0$pNwxblaCJUnQOQsGfp887.'
}

user {"yuchang":
shell=>"/bin/bash",
home=>"/home/yuchang",
ensure=>present,
managehome=>"true",
password=>'$1$Dx1S6$N.hdg8njKNMxp6osFIVAz0'
}

user {"wujuefei":
shell=>"/bin/bash",
home=>"/home/wujuefei",
ensure=>present,
managehome=>"true",
password=>'$1$1p99R1$3wYyntse0yonYSKBeliA21'
}

user {"lixuebin":
shell=>"/bin/bash",
home=>"/home/lixuebin",
ensure=>present,
managehome=>"true",
password=>'$1$ihBZx0$DNRbxIt9wfHKL9Nzy.CxG1'
}

user {"liyangshao":
shell=>"/bin/bash",
home=>"/home/liyangshao",
ensure=>present,
managehome=>"true",
password=>'$1$dXt.r0$KoeXMJf6fiKxtVIb/hcvG.'
}

user {"heguanghao":
shell=>"/bin/bash",
home=>"/home/heguanghao",
ensure=>present,
managehome=>"true",
password=>'$1$UaOa5$ZbBy1B0MxnY8ZuwR7wVNy1'
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
source => "puppet:///modules/online_all/web.sudoers",
path => "/etc/sudoers",
require=>Package["sudo"], 
}

}
