class fordev_user {
user {"for_dev":
shell=>"/bin/bash",
home=>"/home/for_dev",
ensure=>present,
managehome=>"true",
password=>'$1$uQ7kJ1$3zgJ.s1VEjhN8s0Q9UcLS/'
}

file { "for_dev_home":
owner => for_dev,
group => for_dev,
path => "/home/for_dev",
ensure => directory,
mode => 500,
}
}
