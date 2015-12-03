#!/usr/bin/python
# -*- coding: utf-8 -*-
import paramiko


class sys_init(object):
    '''
        系统初始化类
    '''
    def __init__(self):
        pass


    def change_password(self):
        



    def remote_ssh_key_exec(ip,command):
        port = 22
        username = 'root'
        key_file = "/root/.ssh/id_rsa"

        try:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname = ip, username =username, password='',pkey = private_key)
            stdin,stdout,sterr = client.exec_command(command,timeout = 15)
            result = stdout.read()
            error  = sterr.read()
            client.close()
            # print result
            # print error
        except Exception,e:
            print e
            return "wrong",e
        else:
            return result,error
