#!/usr/bin/python
# -*- coding: utf-8 -*-

import paramiko

def remote_ssh_key_exec_simple_online(host,user,command):
    '''
        远程执行 use key
    '''
    key_file = "/root/.ssh/id_dsa"
    private_key = paramiko.DSSKey.from_private_key_file(key_file)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname = host, username = user,pkey  = private_key)
        stdin,stdout,sterr = client.exec_command(command,timeout = 15)
        result = stdout.read()
        error  = sterr.read()
        client.close()

    except Exception,e:
        print e
        return False

    else:
        return result


def trans_file(host,user,pwd,src,dst):
    port = 22
    transport = paramiko.Transport((host,port))
    transport.connect(username = user, password=pwd)
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    try:
        sftp.put(src,dst)
        transport.close()
        sftp.close()

    except Exception,e:
        print e
        return False

    else:
        return True

if __name__ == '__main__':
    src = "/opt/opbin/do_remote/scripts/init_env.sh"
    dst = "/usr/local/src/init_env.sh"
    trans_file('10.134.106.21','root','noSafeNoWork@2014',src,dst)