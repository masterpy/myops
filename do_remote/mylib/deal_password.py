#!/usr/bin/python
# -*- coding: utf-8 -*-
from Crypto.Cipher import AES
from Crypto import Random
import random
#导入基类
from mylib.base import Init_Base

import time,os,string,sys

import pprint

import deal_ssh,common_lib
import re

BS = 32
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(s[-1])]
 
class AESCipher(object):
    def __init__(self, key):
        """
        Requires hex encoded param as a key
        """
        self.key = key.decode("hex")
        
 
    def encrypt( self, raw ):
        """
        Returns hex encoded encrypted value!
        """
        raw = pad(raw)
        iv = Random.new().read(AES.block_size);
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return ( iv + cipher.encrypt( raw ) ).encode("hex")
 
    def decrypt(self,enc):
        
        """
        Requires hex encoded param to decrypt
        """
        enc = enc.decode("hex")
        iv = enc[:16]
        enc= enc[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt(enc))



class PassWorder(object):
    '''
        修改密码类
    '''

    def gernal_password(self,team):
        '''
            生成密码
        '''
        def id_generator(size=6, chars=string.ascii_uppercase + string.digits+'!@#$%^&*()'):
            return ''.join(random.choice(chars) for _ in range(size))

        if team == "dev":
            #password = "sogou_Dev@!~"
            password = "noSafeNoWork@2014"
        elif team == 'qa':
            password = "bizqaapp!@#"
        elif team == 'online':
            password = id_generator(14)

        return password

    
            
class Control_key(Init_Base):
    '''
        管理信任关系类
    '''
    def __init__(self,init_server_info,db_server_info):
        super(Control_key, self).__init__(init_server_info,db_server_info)

    def control_key(self,init_server_info,tag):
        '''
            添加信任关系
        '''
        # BIZOP_KEY = '''from=\\"10.11.199.180,10.13.199.180\\",no-agent-forwarding,no-port-forwarding ssh-dss AAAAB3NzaC1kc3MAAACBAO+yhNAkOZbhvK+CTx1zn6C0CfabaoAZLd2P4OZBi1GR+5S3HUnn9DkfMFXWfvrTBgyUJYWzg76Ymp4hlsZFLV/TR0yhPdIPWYSqAXgerzhx8u3TxxPVpgXzGlXSV424a+6n5XzeQFfj59DvKV4Y1KZqIQNngVkxtDecq2j4SfVfAAAAFQD5YJHwbyzzoV1TUNkNSvZo81ZQ8QAAAIEA19htkFN3vxdrEF571Jt0ACxFBx4xwsrrcbsyrPvJdqxhM85X6EREepIAGs5ronv2y//09WDs/APpoGU/jHwEdhBqXDUJehRzqEbLuY44hLk/DqWiXcrS4mkILqEWqsd5KDG6P1YwG5ezRslf9mrfi9zkGpPmNNATbkB7IMiCvDYAAACBAJcDObyRlj11hBvykYvdA3MU5ywRI8I8w+ldLSoYD3gZ7jVM+dF7H1x5uJFdbi2rXbceJfwABBVQwCh/yamgh+QfjgMoFeJ3/famFd8kqNsw8Y34s4eAVUVv/Xus6KX3OTIiqJjeD1T3pxYKCRLfuATuDSGQAmNhfMikj68w/JGz root@tc_202_117'''
        
        BIZOP_KEY = '''ssh-dss AAAAB3NzaC1kc3MAAACBAO+yhNAkOZbhvK+CTx1zn6C0CfabaoAZLd2P4OZBi1GR+5S3HUnn9DkfMFXWfvrTBgyUJYWzg76Ymp4hlsZFLV/TR0yhPdIPWYSqAXgerzhx8u3TxxPVpgXzGlXSV424a+6n5XzeQFfj59DvKV4Y1KZqIQNngVkxtDecq2j4SfVfAAAAFQD5YJHwbyzzoV1TUNkNSvZo81ZQ8QAAAIEA19htkFN3vxdrEF571Jt0ACxFBx4xwsrrcbsyrPvJdqxhM85X6EREepIAGs5ronv2y//09WDs/APpoGU/jHwEdhBqXDUJehRzqEbLuY44hLk/DqWiXcrS4mkILqEWqsd5KDG6P1YwG5ezRslf9mrfi9zkGpPmNNATbkB7IMiCvDYAAACBAJcDObyRlj11hBvykYvdA3MU5ywRI8I8w+ldLSoYD3gZ7jVM+dF7H1x5uJFdbi2rXbceJfwABBVQwCh/yamgh+QfjgMoFeJ3/famFd8kqNsw8Y34s4eAVUVv/Xus6KX3OTIiqJjeD1T3pxYKCRLfuATuDSGQAmNhfMikj68w/JGz root@tc_202_117'''

        OP_KEY = '''from=\\"10.147.239.235,10.137.239.235,10.146.239.235,10.136.239.235,10.147.239.1,10.137.239.1,10.146.239.1,10.136.239.1\\",no-agent-forwarding,no-port-forwarding ssh-dss AAAAB3NzaC1kc3MAAACBAPx3767ksyO+E+L6fmIKJ+2Uq6yyyk3F83DQ2J+BLZgkzJG6K9FaoFLJQa+iLu3eL9ik+8/oNYcv96dL4M7tZRrQy0swBzIRlEhVRSMN7Ptiu+2TfNfgujA4PVPIvjPqVcbal1frEIy7VHQHSuVMwMI/6edd6J9FAo9CPHnsIlSdAAAAFQCFzOzFUZyUP9cOD+ubopSb+j3z0wAAAIBYXQOIRHmxk0hlwh13seetRtrkNYp1QGkaSLu8KvSr3cmGAUSndqxPVgvL5xT/C3S+sABB4H5KGpxlqTmqNn2MWM+oX4HBmsKXzslxIp0tlwqUE4DWaNvCEiKBqEBnWM+QTlSZ5C0kTJl+Os4rfEYC46R0bhHhYxc6NnpNyYv6JwAAAIBktn02O6k+Tg6CwN1RcG+RMZcqwZaUJ/kgDha3Ho9CZCcC5mNiC36M1qGW0J47RoEe5vSAsTitBgyr3pPEZp5+pnJjaXVo3uRWVtsAodDoWG0dOqYEIeX03VqrFQrt3SBsezPrpKoxZgItSbR6XnkK42iSrgk/f6Eyd3ckbh5a7Q== root@tc_239_235'''

        if tag == "add":
            command = "mkdir -p /root/.ssh && echo \"%s\" > /root/.ssh/authorized_keys && chmod 644 /root/.ssh/authorized_keys" % BIZOP_KEY

            result,error = deal_ssh.remote_ssh_password_exec(init_server_info,command)

            if result == "wrong":
                print "%s 添加key BIZOP_KEY 失败." % init_server_info['client_server']['client_ip']
            else:
                print "%s 添加key BIZOP_KEY 成功." % init_server_info['client_server']['client_ip']

            command = "echo %s >> /root/.ssh/authorized_keys" % OP_KEY
            result,error = deal_ssh.remote_ssh_password_exec(init_server_info,command)

            if result == "wrong":
                print "%s 添加key OP_KEY 失败." % init_server_info['client_server']['client_ip']
            else:
                print "%s 添加key OP_KEY 成功." % init_server_info['client_server']['client_ip']

        elif tag == "del":
            command = "sed -i 's/root@tc_202_117//g' /root/.ssh/authorized_keys"
            result,error = deal_ssh.remote_ssh_password_exec(init_server_info,command)
            if result == "wrong":
                print "删除key OP_KEY 失败."
            else:
                print "删除key OP_KEY 成功"



    def add_relation_server(self):
        '''
            添加信任关系
        '''
        for init_server_info in self.init_server_info:
            self.control_key(init_server_info,'add')


    def del_relation_server(self):
        '''
            删除信任关系
        '''
        relation_cls = Control_key()
        relation_cls.control_key('del')  

    def change_server_password(self,new_password,server_info):
        '''
            改变服务器密码
        '''
        user = server_info['client_server']['client_user']
        _command = 'echo \"%s\" | passwd %s --stdin' % (new_password,user)
        result,error = deal_ssh.remote_ssh_key_exec(server_info,_command)

        if result == "wrong":
            print "%s change password failed." %  server_info['client_server']['client_ip']
            return False
        else:
            print "%s change password sucess."  % server_info['client_server']['client_ip']
            return True

    def set_server_status(self):
        '''
            设置服务器状态信息
        '''
        relase,hostname,idcname,host_busi_ip,host_data_ip = "","","","",""
        eth0_mac,eth1_mac,eth2_mac,eth3_mac = "","","",""
        server_manufacturer,server_sn,product_name = "","",""

        temp_dic = {}
        temp_list = []
        password_cls = PassWorder()

        for server_info in self.init_server_info:
            temp_dic = server_info['client_server'].copy()


            new_password = password_cls.gernal_password(temp_dic['group'])
            temp_dic['new_password'] = new_password
            self.change_server_password(new_password,server_info)
            
            relase = common_lib.get_system_release(server_info)
            hostname = common_lib.get_system_hostname(server_info)

            if common_lib.get_idc_name(temp_dic['client_ip']):
                idcname,host_busi_ip,host_data_ip = common_lib.get_idc_name(temp_dic['client_ip'])
            else:
                print "get_idc_name failed."
            
            if common_lib.get_adapter_mac(server_info):
                eth0_mac,eth1_mac,eth2_mac,eth3_mac = common_lib.get_adapter_mac(server_info)
            else:
                print "get_adapter_mac failed."

            if common_lib.get_system_product(server_info):
                server_manufacturer,server_sn,product_name = common_lib.get_system_product(server_info)
            else:
                print "get_system_product failed."


            temp_dic['client_hostname'] = hostname
            temp_dic['client_relase'] = relase
            temp_dic['idc_name'] = idcname
            temp_dic['host_busi_ip'] = host_busi_ip
            temp_dic['host_data_ip'] = host_data_ip
            temp_dic['eth0_mac'] = eth0_mac
            temp_dic['eth1_mac'] = eth1_mac
            temp_dic['eth2_mac'] = eth2_mac
            temp_dic['eth3_mac'] = eth3_mac
            temp_dic['server_manufacturer'] = server_manufacturer
            temp_dic['server_sn'] = server_sn
            temp_dic['product_name'] = product_name
            temp_dic['cloud_type'] = self.judge_cloud_type(temp_dic['server_package'])
        
        
            self.save_server_info(temp_dic)
            temp_dic = {}


    def judge_cloud_type(server_package):
        '''
            判断虚机属于公有云还是私有云
        '''
        priv_cloud_type = re.compile("(^V[0-9]-[0-9])")
        pub_cloud_type = re.compile("(^U[0-9])")

        if priv_cloud_type.match(server_package):
            cloud_type = "private_vm_machine"

        elif pub_cloud_type.match(server_package):
            cloud_type = "public_vm_machine"

        else:
            cloud_type = "physical_pm_machine"

        return cloud_type


    def encrypt_password(self,new_password):
        '''
            保存密码至mysql数据库
            data_list: 主机信息列表
        '''
        modify_date =  time.strftime("%Y-%m-%d",time.localtime())

        key = "6QqnsHGibwaGt4jkZxGmBpeYngNnqMqJ"
        key=key[:32].encode("hex")
        decryptor = AESCipher(key)
        plaintext = decryptor.encrypt(new_password)

        return plaintext
        

    def save_server_info(self,client_info):
        '''
            保存服务器状态信息
        '''
        server_type  = client_info['machine_type']
        new_password = client_info['new_password']
        host_data_ip = client_info['host_data_ip']
        host_busi_ip = client_info['host_busi_ip']
        eth0_mac = client_info['eth0_mac']
        eth1_mac = client_info['eth1_mac']
        eth2_mac = client_info['eth2_mac']
        eth3_mac = client_info['eth3_mac']
        idc_name = client_info['idc_name']
        user = client_info['client_user']
        relase = client_info['client_relase']
        host_name = client_info['client_hostname']
        server_manufacturer = client_info['server_manufacturer']
        server_sn = client_info['server_sn']
        product_name =  client_info['product_name']
        plaintext = self.encrypt_password(new_password)
        modify_date =  time.strftime("%Y-%m-%d",time.localtime())
        cloud_type = client_info['cloud_type']
        

        sql = "select `id` from server_info where host_busi_ip = '%s' or server_sn = '%s'" 
        result = super(Control_key,self).select_advanced(sql,host_busi_ip,server_sn)



        if len(result) > 0:
            for sn in result:
                    conditional_query_two = 'id = %s '
                    super(Control_key,self).update('server_info', conditional_query_two,sn,host_data_ip=host_data_ip,host_busi_ip=host_busi_ip,host_name=host_name,user_account=user,root_password=plaintext,server_release=relase,server_type=server_type,cloud_type=cloud_type,server_manufacturer=server_manufacturer,server_sn=server_sn,product_name=product_name,eth0_mac=eth0_mac,eth1_mac=eth1_mac,eth2_mac=eth2_mac,eth3_mac=eth3_mac,idc_name=idc_name,modify_date=modify_date)
        else:
            super(Control_key,self).insert('server_info',host_data_ip=host_data_ip,host_busi_ip=host_busi_ip,host_name=host_name,user_account=user,root_password=plaintext,server_release=relase,server_type=server_type,cloud_type=cloud_type,server_manufacturer=server_manufacturer,server_sn=server_sn,product_name=product_name,eth0_mac=eth0_mac,eth1_mac=eth1_mac,eth2_mac=eth2_mac,eth3_mac=eth3_mac,idc_name=idc_name,modify_date=modify_date)  

