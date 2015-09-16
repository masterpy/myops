#!/usr/bin/python
# -*- coding: utf-8 -*-
from mysql_cls import MysqlPython
import deal_ssh,common_lib
import StringIO
import re,sys,time,string
import pprint 
import re

import paramiko

'''
    处理一些工具的小功能
'''



class Tools_cls(object):
    '''
        处理小工具类
    '''
    def __init__(self,init_server_info,ca_info):
        self.init_server_info = init_server_info
        self.ca_info          = ca_info
        

    def add_hostname(self):
        '''
            添加hostname 清理原有hostname
        '''
        inner_domain = "sogou-in.domain"
        look_hosts_cmd = "cat /etc/hosts"
        look_network_cmd = "cat /etc/sysconfig/network"
        short_host_name = ""

        for server_info in self.init_server_info: 
            host_ip = server_info['client_server']['client_ip']

            if common_lib.get_idc_name(host_ip.strip()):
                idcname,host_busi_ip,host_data_ip = common_lib.get_idc_name(host_ip)
            else:
                print "get_idc_name failed."

            #hostname信息
            result,error = deal_ssh.remote_ssh_key_exec(server_info,look_network_cmd)
            if result == "wrong":
                print "host: %s . get host info failed." %  server_info['client_server']['client_ip']

            buf = StringIO.StringIO(result)
            for line in buf.readlines():
                line = line.strip()
                if line.startswith("HOSTNAME"):
                    short_host_name = line.split("=")[1]
            
            hostname = short_host_name + "." + inner_domain
            p1 = re.compile("(.*)%s()"  % short_host_name)
            #hostname信息
            result,error = deal_ssh.remote_ssh_key_exec(server_info,look_hosts_cmd)
            if result == "wrong":
                print "host: %s . get host info failed." %  server_info['client_server']['client_ip']
            buf = StringIO.StringIO(result)
            for line in buf.readlines():
                line = line.strip()
                if p1.match(line):
                    delete_old_cmd = "sed -i /%s/d /etc/hosts" % short_host_name
                    deal_ssh.remote_ssh_key_exec(server_info,delete_old_cmd)
                    if result == "wrong":
                        print "host: %s . delete host info failed." %  server_info['client_server']['client_ip']
            add_hostname = "%s   %s   %s" %  (host_data_ip,hostname,short_host_name)
            add_hostname_cmd = "echo -e \"%s\" >> /etc/hosts" % add_hostname
            deal_ssh.remote_ssh_key_exec(server_info,add_hostname_cmd)

            return hostname


    def clean_ca_cert(self,hostname):
        '''
            清理CA证书
        '''
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ca_host  = self.ca_info['ca_host_ip']
        ca_user  = self.ca_info['ca_host_user']
        ca_pass  = self.ca_info['ca_host_password']
        clean_cmd = "puppet cert -c %s" % hostname

        try:
            ssh.connect(hostname = ca_host, username = ca_user, password=ca_pass)
            stdin,stdout,stderr = ssh.exec_command(clean_cmd)
            result = stdout.read()
            error  = stderr.read()
        except Exception,e:
            print "host: %s,%s" % (host,e)
            return False
        else:
            return True
    

    def check_404_user(self,ip):
        '''
            检查用户
        '''
        result = ""
        user = "for_monitor"
        cmd = "cat /etc/passwd  | grep -E \"wangshuai|lixuebin\" | cut -d \":\" -f1"
        result = deal_ssh.remote_ssh_key_exec_simple(ip,user,cmd)
        print ip
        print result

        if result:
            f = open('/tmp/404.list','a+')
            f.write(ip)
            f.write("\n")
            f.write(result)
            f.write("\n")
            f.write("%s" % "="*20)
            f.write("\n")
            f.close()

