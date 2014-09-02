# -*- coding: utf-8 -*-
#!/usr/bin/python
from ConfigParser import ConfigParser
import os
import pwd
from subprocess import Popen,PIPE
import time


class Gernal_conf(ConfigParser):
    def __init__(self,config):
        '''
            必须初始化ConfigParser类，否则无法获取section
        '''
        ConfigParser.__init__(self)
        self.ftpvars={}
        self.config = config

    def set_log_value(self,kw):
        '''
            取出默认值，保存入字典
        '''
        for k,v in kw.items():
            self.ftpvars[k]=v
            setattr(self, k ,v)


    def set_log_default_value(self):
        '''
            设置默认值
        '''
        default_value={
                        "smtpserver":"smtp.juren.com",
                        "sender":"server_alarm@juren.com",
                        "password":"jr123456",
                        "receiver":"wangrui@juren.com  xinjianguo@juren.com",
                        "subject":"\'Server %s Tomcat Error Log Online\'" % self.server_ip(),
                        "tomcat_log" : "/tmp/out.log",
                        "error_log_file" : "/tmp/%s.out.log.gz"  % self.server_ip(),
                        "#### = log_time like 2 hours or 1 days or 10 minutes":"#######",
                        "log_time" : "2 hours",
                        "#### = buffer means file read buffer":"#############",
                        "buffer" : "8196"

                       }
        self.set_log_value(default_value)

    def save(self):
        if not self.has_section('mail_conf'):
            self.add_section('mail_conf')

        for k,v in self.ftpvars.items():
            self.set('mail_conf',k,v)

        with open (self.config,'w') as ftpconf:
            self.write(ftpconf)



    def get_value(self,config):
        '''
            读取配置文件
        '''
        args={}
        self.read(config)
        options = self.options('mail_conf')
        for values in options:
            args[values] = self.get('mail_conf',values)
        return args

    def server_ip(self):
        cmd = "ifconfig eth0"
        result = Popen(cmd,stdout=PIPE,shell=True)
        for line in result.stdout.readlines():
            if line.strip().startswith("inet addr"):
                 ip = line.split(":")[1].split()[0]
        return ip

