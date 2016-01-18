#!/usr/bin/python
# -*- coding: utf-8 -*-
import paramiko,os
import common_lib,logger


class Ssh_Cls(object):
    def __init__(self,host):
        '''
            初始化类
        '''
        self.host = host
        init_server_info = common_lib.get_remote_server_info('init.conf')
        self.default_user = init_server_info['client_server']['client_user']
        self.default_client_password = init_server_info['client_server']['client_password']
        self.client_port = init_server_info['client_server']['client_port']
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname = self.host, username = self.default_user, password =self.default_client_password)

    def do_remote_by_passwd_exec(self,command):
        '''
            默认账号密码
        '''
        try:
            stdin,stdout,sterr = self.ssh.exec_command(command,timeout = 15)
            result = stdout.read()
            error  = sterr.read()
        except Exception,e:
                logger.write_log(e)
                return "wrong",e
        else:
            if len(result) == 0 and len(error) > 0:
                logger.write_log(error)
                return "wrong",error
            return result,error

    def close_ssh(self):
        '''
            关闭ssh连接
        '''
        self.ssh.close()
