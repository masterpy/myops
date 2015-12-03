#!/usr/bin/python
# -*- coding: utf-8 -*-
import paramiko,os

def remote_ssh_key_exec(remote_server_info,command):
    '''
        远程执行 use key
    '''
    key_file = "/root/.ssh/id_dsa"
    #key_file = "D:/temp/id_rsa"
    private_key = paramiko.DSSKey.from_private_key_file(key_file)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


    if 'client_server' in remote_server_info:
        for key,value in remote_server_info.items():
            if key == "client_server":
                host = value['client_ip']
                user = value['client_user']
            try:
                client.connect(hostname = host, username = user, password='',pkey = private_key)
                stdin,stdout,sterr = client.exec_command(command,timeout = 15)
                result = stdout.read()
                error  = sterr.read()
                client.close()

            except Exception,e:
                print e
                return "wrong",e
            else:
                print error
                if len(result) == 0 and len(error) > 0:
                   return "wrong",error
                return result,error


def remote_ssh_password_exec(remote_server_info,command):
    '''
        远程执行 use key
    '''
    import sys
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()

    if 'client_server' in remote_server_info:
        for key,value in remote_server_info.items():
            if key == "client_server":
                host = value['client_ip']
                port = int(value['client_port'])
                user = value['client_user']
                password = value['client_password']
                try:
                    ssh.connect(hostname = host, username = user, password=password)
                    stdin,stdout,stderr = ssh.exec_command(command)
                    result = stdout.read()
                    error  = stderr.read()
                except Exception,e:
                    print "host: %s,%s" % (host,e)
                    sys.exit(1)
                    return "wrong",e
                else:
                    if len(result) == 0 and len(error) > 0:
                        return "wrong",error
                    return result,error

def remote_ssh_key_exec_simple_online(host,user,command):
    '''
        远程执行 use key
    '''
    key_file = "/root/.ssh/id_dsa"
    private_key = paramiko.DSSKey.from_private_key_file(key_file)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    logger = paramiko.util.logging.getLogger()
    paramiko.util.log_to_file('filename.log')

    try:
        client.connect(hostname = host, username = user, password='',pkey = private_key)
        stdin,stdout,sterr = client.exec_command(command,timeout = 15)
        result = stdout.read()
        error  = sterr.read()
        client.close()

    except Exception,e:
        print e
        return False

    else:
        return result

def remote_ssh_password_simple_online(host,user,passwd,cmd):
    '''
        处理密码
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname = host, username = user, password=passwd)
        stdin,stdout,stderr = ssh.exec_command(cmd)
        result = stdout.read()
        error  = stderr.read()
        ssh.close()

    except Exception,e:
        return False
    else:
        return result




def remote_ssh_key_exec_simple(host,user,command):
    '''
        远程执行 use key
    '''
    key_file = "/root/.ssh/id_dsa"
    private_key = paramiko.DSSKey.from_private_key_file(key_file)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    logger = paramiko.util.logging.getLogger()
    paramiko.util.log_to_file('filename.log')

    try:
        client.connect(hostname = host, username = user, password='',pkey = private_key)
        stdin,stdout,sterr = client.exec_command(command,timeout = 15)
        result = stdout.read()
        error  = sterr.read()
        client.close()

    except Exception,e:
        print e
        return False

    else:
        #return True
        return result

def remote_ssh_password_simple(host,user,passwd,cmd):
    '''
        处理密码
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname = host, username = user, password=passwd)
        stdin,stdout,stderr = ssh.exec_command(cmd)
        result = stdout.read()
        error  = stderr.read()
        ssh.close()

    except Exception,e:
        return False
    else:
        #return True
        return result

def remote_scp(host,user):
    '''
        处理密码
    '''
    port = 22
    key_file = "/root/.ssh/id_dsa"

    transport = paramiko.Transport((host,port))
    private_key = paramiko.DSSKey.from_private_key_file(key_file)
    transport.connect(username=user,pkey = private_key)
    sftptest = paramiko.SFTPClient.from_transport(transport)

    try:
        sftptest.put('/opt/opbin/do_remote/scripts/puppet_up.sh', '/home/for_monitor/puppet_up.sh')
        transport.close()
        sftptest.close()

    except Exception,e:
        print e
        return False

    else:
        return True
        #return result

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