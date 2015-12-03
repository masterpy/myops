#!/usr/bin/python
# -*- coding: utf-8 -*-
from mysql_cls import MysqlPython
import deal_ssh,common_lib
import StringIO
import re,sys,time,string
import pprint 
import re
import time
import paramiko

'''
    处理一些工具的小功能
'''

class Tools_cls(object):
    '''
        处理小工具类
    '''
    def __init__(self,machine_ip_list,ca_info,client_info):
        self.ca_info     = ca_info
        self.client_info = client_info
        self.host_ip_list = machine_ip_list

    def add_hostname(self):
        '''
            添加hostname 清理原有hostname
        '''
        remote_user = self.client_info['client_user']
        remote_passwd = self.client_info['client_password']
        remote_port = self.client_info['client_port']

        inner_domain = "sogou-in.domain"
        look_hosts_cmd = "cat /etc/hosts"
        look_network_cmd = "cat /etc/sysconfig/network"
        short_host_name = ""
        hostname_list = []

        for host_ip in self.host_ip_list:
            print host_ip
            if common_lib.get_idc_name(host_ip.strip()):
                idcname,host_busi_ip,host_data_ip = common_lib.get_idc_name(host_ip)
            else:
                return {'status': "failed",'msg':"%s  host: %s,get_idc_name failed." % (time.strftime("%Y-%m-%d %H:%M",time.localtime()),host_ip)}

            #hostname信息
            result  = deal_ssh.remote_ssh_password_simple_online(host_ip,remote_user,remote_passwd,look_network_cmd)
            
            if isinstance(result,bool):
                return {'status': "failed",'msg':"%s  host: %s,get host info failed." % (time.strftime("%Y-%m-%d %H:%M",time.localtime()),host_ip)}

            buf = StringIO.StringIO(result)
            for line in buf.readlines():
                line = line.strip()
                if line.startswith("HOSTNAME"):
                    short_host_name = line.split("=")[1]
            
            hostname = short_host_name + "." + inner_domain
            p1 = re.compile("(.*)%s()"  % short_host_name)
            #hostname信息
            result  = deal_ssh.remote_ssh_password_simple_online(host_ip,remote_user,remote_passwd,look_hosts_cmd)
            
            if isinstance(result,bool):
                return {'status': "failed",'msg':"%s  host: %s,get host info failed." % (time.strftime("%Y-%m-%d %H:%M",time.localtime()),host_ip)}

            buf = StringIO.StringIO(result)
            for line in buf.readlines():
                line = line.strip()
                if p1.match(line):
                    delete_old_cmd = "sed -i /%s/d /etc/hosts" % short_host_name
                    deal_ssh.remote_ssh_password_simple_online(host_ip,remote_user,remote_passwd,delete_old_cmd)
            
            #添加hostname
            add_hostname = "%s   %s   %s" %  (host_data_ip,hostname,short_host_name)
            add_hostname_cmd = "echo -e \"%s\" >> /etc/hosts" % add_hostname

            deal_ssh.remote_ssh_password_simple_online(host_ip,remote_user,remote_passwd,add_hostname_cmd)

            hostname_list.append(hostname)
        return hostname_list



    def clean_ca_cert(self,remote_hostname_list):
        '''
            清理CA证书
        '''
        clean_cmd_all = ""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ca_host  = self.ca_info['ca_host_ip']
        ca_user  = self.ca_info['ca_host_user']
        ca_pass  = self.ca_info['ca_host_password']
        
        for remote_hostname in remote_hostname_list:
            clean_cmd = "puppet cert -c %s;" % remote_hostname
            clean_cmd_all += clean_cmd

        try:
            ssh.connect(hostname = ca_host, username = ca_user, password=ca_pass)
            stdin,stdout,stderr = ssh.exec_command(clean_cmd_all)
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

