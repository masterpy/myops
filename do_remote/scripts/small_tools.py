#!/usr/bin/python
# -*- coding: utf-8 -*-
from mysql_cls import MysqlPython
import deal_ssh,common_lib
import StringIO
import re,sys,time,string,os
import pprint,subprocess,shlex
import re

'''
    处理一些工具的小功能
'''

def add_hostname_temp(ip):
    '''
        添加hostname 清理原有hostname
    '''
    inner_domain = "sogou-in.domain"
    look_hosts_cmd = "cat /etc/hosts"
    look_network_cmd = "cat /etc/sysconfig/network"
    short_host_name = ""

    user = "root"
    #hostname信息
    result = deal_ssh.remote_ssh_key_exec_simple(ip,user,look_network_cmd)

    buf = StringIO.StringIO(result)
    for line in buf.readlines():
        line = line.strip()
        if line.startswith("HOSTNAME"):
            short_host_name = line.split("=")[1]
            

    hostname = short_host_name + "." + inner_domain
    p1 = re.compile("(.*)%s()"  % short_host_name)
        
    result = deal_ssh.remote_ssh_key_exec_simple(ip,user,look_network_cmd)
        
    buf = StringIO.StringIO(result)
    for line in buf.readlines():
        line = line.strip()
        if p1.match(line):
            delete_old_cmd = "sed -i /%s/d /etc/hosts" % short_host_name
            deal_ssh.remote_ssh_key_exec_simple(ip,user,delete_old_cmd)

        
    add_hostname = "%s   %s   %s" %  (ip,hostname,short_host_name)

    add_hostname_cmd = "echo -e \"%s\" >> /etc/hosts;hostname -f" % add_hostname
    
    result = deal_ssh.remote_ssh_key_exec_simple(ip,user,add_hostname_cmd)

    add_hostname_cmd = "sed -i /houston.repos.sogou-inc.com/d /etc/hosts;echo -e \"10.139.45.69   houston.repos.sogou-inc.com\" >> /etc/hosts"

    result = deal_ssh.remote_ssh_key_exec_simple(ip,user,add_hostname_cmd)

    print result

def change_tmp_power(ip):
    users = ["lixuebin","lizhi","wangwei","gaozezhou","heguanghao","dongyuntao","liyangshao","yuchang","wujuefei","zhangchengshan","wangshuai","for_dev"]

    for user in users:
        cmd = "sudo setfacl -m u:%s:r-x /tmp" % user
        user = "for_monitor"
        result = deal_ssh.remote_ssh_key_exec_simple(ip,user,cmd)
        
        if isinstance(result,bool):
            print ip
            return False
        else:
            pass


def change_dir(ip):
    user = "root"
    cmd = "umount /search;sed -i s/search/data/g /etc/fstab;mkdir /data ; mount -a;df -h"
    #cmd = "cat /etc/passwd | grep \"for_monitor\""
    #cmd = "sed '/tc_202_117/d' ~/.ssh/authorized_keys"
    result = deal_ssh.remote_ssh_key_exec_simple(ip,user,cmd)
    
    if isinstance(result,bool):
        print ip
        return False
    else:
        pass

    #print "host:%s success!" % ip
    #cmd = 'echo \"%s\" | passwd %s --stdin' % (new_password,user)

    # user = "root"
    #cmd = "rm -rf /var/lib/puppet/*;umount /search;sed -i s/search/data/g /etc/fstab;mkdir /data ; mount -a;df -h;puppet agent -t"
    #cmd = "ls"
    #result = deal_ssh.remote_ssh_password_simple(ip,user,new_password,cmd)
    
    #print result
    


def install_soft(hostip):
    result = False

    user = "root"

    scripts_dir = "/opt/opbin/do_remote/scripts"
    file_name = "%s/%s" % (scripts_dir,"init_env.sh")
    
    install_dir = "/usr/local/src/"


    cmd_local = "rsync -auv %s %s:%s" % (file_name,hostip,install_dir)
    print cmd_local
    child1 = subprocess.call(shlex.split(cmd_local), stdout=subprocess.PIPE)  
    cmd_remote = "cd %s;bash %s" % (install_dir,"init_env.sh")

    if child1 == 0:
        result = deal_ssh.remote_ssh_key_exec_simple(hostip,user,cmd_remote)
        print result
        if result:
            print "soft install success!"
            return True

    print "install soft sucess!"


def del_key(ip):
    cmd = "sed '/tc_202_117/d' ~/.ssh/authorized_keys"
    user = "root"
    result = deal_ssh.remote_ssh_key_exec_simple(ip,user,cmd)
    if len(result) > 0:
        print result
    else:
        print ip 


def set_password(ip):
    '''
        修改密码
    '''
    import random
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits+'&%+-()'):
        return ''.join(random.choice(chars) for _ in range(size))

    new_password = id_generator(14)
    user = "for_monitor"
    host  = ip 

    command = '''str=$((echo \"%s\";echo \"%s\")|sudo /sbin/grub-md5-crypt 2>/dev/null | grep -iv \"password\");sudo cat /etc/shadow | awk -v str=$str -F ':' '{OFS=":"}{if($1~/root/){sub(/.*/,str,$2);}print }' > ~/shadow;sudo /bin/cp -f ~/shadow /etc/shadow;sudo chown root:root /etc/shadow;sudo chmod 400 /etc/shadow;rm -f ~/shadow''' % (new_password,new_password) 


    f = open("/tmp/machine.list.pass","a+")
    f.write(ip)
    f.write(" ")
    f.write(new_password)
    f.write("\n")
    result = deal_ssh.remote_ssh_key_exec_simple(host,user,command)
    
    if result:
        pass
    else:
        print "%s failed" % ip
        

    cmd = "ls"
    root_user = "root"
    if deal_ssh.remote_ssh_password_simple(host,root_user,new_password,cmd):
        pass
    else:
        print "host: %s, exec failed!" % ip

def check_default_password(ip):
    '''
        检查默认密码
    '''
    import random
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits+'@#$%^&*()'):
        return ''.join(random.choice(chars) for _ in range(size))

    new_password = id_generator(14)


    user = "root"
    #cmd = "ifconfig eth0 | grep \"inet addr\" | cut -d \":\" -f2"
    _command = 'echo \'%s\' | passwd %s --stdin' % (new_password,user)
    host  = ip 
    user  = "root"
    passwd  = "noSafeNoWork@2014"
    try:
        deal_ssh.remote_ssh_password_simple(host,user,passwd,_command)
    except Exception,e:
        print e
        return False
    else:
        cmd = "hostname -f"
        if  deal_ssh.remote_ssh_password_simple(host,user,new_password,cmd):
            f = open('/tmp/machine.list.pass','a+')
            f.write(ip)
            f.write(",")
            f.write(new_password)
            f.write("\n")
            f.close()
            return True
        else:
            print ip

def check_passwd(ip,new_password):
    #os.popen("mv /root/.ssh /root/.ssh.BAK")
    cmd = "ls"
    root_user = "root"
    if deal_ssh.remote_ssh_password_simple(ip,root_user,new_password,cmd):
        print "host: %s, exec ok!" % ip
        return True
    else:
        print "host: %s, exec failed!" % ip
        f = open ("/tmp/error.ip",'a+')
        f.write("%s" % ip)
        f.write("\n")
        f.close()
        print "host: %s, exec failed!" % ip
        return False


def add_relation(ip):

    USER = "for_monitor"
    OP_KEY = '''from=\\"10.147.239.235,10.137.239.235,10.146.239.235,10.136.239.235,10.147.239.1,10.137.239.1,10.146.239.1,10.136.239.1\\",no-agent-forwarding,no-port-forwarding ssh-dss AAAAB3NzaC1kc3MAAACBAPx3767ksyO+E+L6fmIKJ+2Uq6yyyk3F83DQ2J+BLZgkzJG6K9FaoFLJQa+iLu3eL9ik+8/oNYcv96dL4M7tZRrQy0swBzIRlEhVRSMN7Ptiu+2TfNfgujA4PVPIvjPqVcbal1frEIy7VHQHSuVMwMI/6edd6J9FAo9CPHnsIlSdAAAAFQCFzOzFUZyUP9cOD+ubopSb+j3z0wAAAIBYXQOIRHmxk0hlwh13seetRtrkNYp1QGkaSLu8KvSr3cmGAUSndqxPVgvL5xT/C3S+sABB4H5KGpxlqTmqNn2MWM+oX4HBmsKXzslxIp0tlwqUE4DWaNvCEiKBqEBnWM+QTlSZ5C0kTJl+Os4rfEYC46R0bhHhYxc6NnpNyYv6JwAAAIBktn02O6k+Tg6CwN1RcG+RMZcqwZaUJ/kgDha3Ho9CZCcC5mNiC36M1qGW0J47RoEe5vSAsTitBgyr3pPEZp5+pnJjaXVo3uRWVtsAodDoWG0dOqYEIeX03VqrFQrt3SBsezPrpKoxZgItSbR6XnkK42iSrgk/f6Eyd3ckbh5a7Q== root@tc_239_235'''

    command = "sudo mkdir -p /root/.ssh;sudo cat /root/.ssh/authorized_keys >  ~/authorized_keys;sudo sed -i '/tc_239_235/d' ~/authorized_keys;sudo echo \"%s\" >> ~/authorized_keys;sudo /bin/cp ~/authorized_keys  /root/.ssh/;sudo chmod 600 /root/.ssh/authorized_keys; rm -f ~/authorized_keys" % OP_KEY
    
    result = deal_ssh.remote_ssh_key_exec_simple(ip,USER,command)

    if result:
        pass
    else:
        print "host:%s add relation failed!"  % ip
        f = open('/tmp/add_relation.result','a+')
        f.write("host:%s add relation failed!"  % ip)
        f.write("\n")
        f.close()

def del_relation(ip):
    USER = "for_monitor"
    command  = "sudo sed -i '/tc_239_235/d' /root/.ssh/authorized_keys"
    result = deal_ssh.remote_ssh_key_exec_simple(ip,USER,command)
    print result



def set_password_only(host,password):

    user  = "root"
    _command = 'echo \'%s\' | passwd %s --stdin' % (password,user)
    print host
    print _command
    host  = ip 
    user  = "root"
    passwd  = "noSafeNoWork@2014"
    deal_ssh.remote_ssh_key_exec_simple(host,user,_command)


def clean_ca(hostname):
    '''
        清理CA
    '''
    ca_server = '10.134.33.223'
    ca_pass = 'T9MJ?SSI'
    root_user = 'root'

    cmd = "puppet cert -c %s" % hostname
    deal_ssh.remote_ssh_password_simple(ca_server,root_user,ca_pass,cmd)

def clean_dns(ip):
    user = "root"
    cmd = "sed -i '/houston.repos.sogou-inc.com/d' /etc/hosts"
    deal_ssh.remote_ssh_key_exec_simple(ip,user,cmd)


def check_puppet_version(ip):
    '''
        检查puppet 版本
    '''
    p = re.compile("^puppet-0\.25\.5.*")
    command  = "rpm -qa |grep \"^puppet-\""
    #command = "sudo sed -i '/10.144.224.86/d' /etc/hosts;sudo sed -i '/10.144.224.82/d' /etc/hosts;sudo service mcollective stop;sudo chkconfig mcollective off"

    get_hostname_cmd = "hostname -f"

    install_command = "sudo bash puppet_up.sh;test $? == 0 && rm -f /home/for_monitor/puppet_up.sh"

    user = "for_monitor"
    result = deal_ssh.remote_ssh_key_exec_simple(ip,user,command)
    print "result:%s ip:%s" % (result,ip)
    if isinstance(result,bool):
        f = open("/tmp/puppet_error.ip",'a+')
        f.write("%s" % ip)
        f.close()
        return False
    else:
        pass


    if p.match(result.strip().strip("\n")):
        f = open("/tmp/puppet_exec.ip",'a+')
        f.write("%s : ok" % ip)
        f.write("\n")
        f.close()

        # hostname = deal_ssh.remote_ssh_key_exec_simple(ip,user,get_hostname_cmd)
        # clean_ca(hostname)

        # deal_ssh.remote_scp(ip,user)
        # result = deal_ssh.remote_ssh_key_exec_simple(ip,user,install_command)


        # result =  deal_ssh.remote_ssh_key_exec_simple(ip,user,command)

        # if p.match(result.strip().strip("\n")):
        #     print "host: %s exec sucess!" % ip
        # else:
        #     f = open("/tmp/puppet_error.ip",'a+')
        #     f.write("%s : error" % ip)
        #     f.write("\n")
        #     f.close()


if __name__ == '__main__':
    temp1 = []
    temp2 = []

    #with open("/tmp/machine.list.pass") as f:
    #with open("/opt/opbin/tools/temp.list") as f:
    with open("/opt/opbin/tools/temp.list") as f:
        for line in f.readlines():
            ip = line.strip()
            #del_relation(ip)
            #add_relation(ip)
            add_hostname_temp(ip)
            check_default_password(ip)
            change_dir(ip)
            install_soft(ip)
            clean_dns(ip)
  
        # with open("/tmp/machine.list.pass2") as f:
        #     for line in f.readlines():
        #         if len(line) > 1:
        #             old_ip = line.strip().split(",")[0]
        #             pwd = line.strip().split(",")[1]
        #             if old_ip == ip:
        #                 if check_passwd(ip,pwd):
        #                     print ip

    #os.popen("mv /root/.ssh.BAK /root/.ssh")
                        #del_key(ip)
    # temp1 = []
    # temp2 = []
    # with  open("/tmp/machine.list.pass3") as f1:
    #     temp1 =  f1.readlines()

    # with open("/tmp/error.ip") as f2:
    #     temp2 = f2.readlines()


    # for line1 in temp1:
    #     ip = line1.split()[0]
    #     passwd = line1.split()[1]
    #     for line2 in temp2:
    #         line2 = line2.strip()
    #         if ip == line2:
    #             set_password_only(ip,passwd)
                #check_passwd(ip,passwd)
                    #print d1
                #     line = line.strip()
                #     ip = line.split()[0]
                #     passwd = line.split()[1]
                #     line2 = line2.strip()
                #     print ip
                #     if ip == line2:
                #         pass
                        #print ip
                #check_passwd(ip,passwd)


   # with  open("/tmp/machine.list.pass3") as f1:
   #      for line in f1.readlines():
   #          ip = line.split()[0]
   #          passwd = line.split()[1]
   #          check_passwd(ip,passwd)