#!/usr/bin/python
# -*- coding: utf-8 -*-
from mylib.base import Init_Base

import time,os,string,sys
import deal_ssh,common_lib,logger,deal_gernal_password
import re
import StringIO
import paramiko


class Control_key(Init_Base):
    '''
        管理信任关系类
    '''
    def __init__(self,db_server_info,ssh_con):
        super(Control_key,self).__init__(db_server_info)
        self.ssh_con = ssh_con

    def control_key(self,host_ip):
        '''
            添加信任关系
        '''
        BIZOP_KEY = '''ssh-dss AAAAB3NzaC1kc3MAAACBAO+yhNAkOZbhvK+CTx1zn6C0CfabaoAZLd2P4OZBi1GR+5S3HUnn9DkfMFXWfvrTBgyUJYWzg76Ymp4hlsZFLV/TR0yhPdIPWYSqAXgerzhx8u3TxxPVpgXzGlXSV424a+6n5XzeQFfj59DvKV4Y1KZqIQNngVkxtDecq2j4SfVfAAAAFQD5YJHwbyzzoV1TUNkNSvZo81ZQ8QAAAIEA19htkFN3vxdrEF571Jt0ACxFBx4xwsrrcbsyrPvJdqxhM85X6EREepIAGs5ronv2y//09WDs/APpoGU/jHwEdhBqXDUJehRzqEbLuY44hLk/DqWiXcrS4mkILqEWqsd5KDG6P1YwG5ezRslf9mrfi9zkGpPmNNATbkB7IMiCvDYAAACBAJcDObyRlj11hBvykYvdA3MU5ywRI8I8w+ldLSoYD3gZ7jVM+dF7H1x5uJFdbi2rXbceJfwABBVQwCh/yamgh+QfjgMoFeJ3/famFd8kqNsw8Y34s4eAVUVv/Xus6KX3OTIiqJjeD1T3pxYKCRLfuATuDSGQAmNhfMikj68w/JGz root@tc_202_117'''

        OP_KEY = '''from=\\"10.147.239.235,10.137.239.235,10.146.239.235,10.136.239.235,10.147.239.1,10.137.239.1,10.146.239.1,10.136.239.1\\",no-agent-forwarding,no-port-forwarding ssh-dss AAAAB3NzaC1kc3MAAACBAPx3767ksyO+E+L6fmIKJ+2Uq6yyyk3F83DQ2J+BLZgkzJG6K9FaoFLJQa+iLu3eL9ik+8/oNYcv96dL4M7tZRrQy0swBzIRlEhVRSMN7Ptiu+2TfNfgujA4PVPIvjPqVcbal1frEIy7VHQHSuVMwMI/6edd6J9FAo9CPHnsIlSdAAAAFQCFzOzFUZyUP9cOD+ubopSb+j3z0wAAAIBYXQOIRHmxk0hlwh13seetRtrkNYp1QGkaSLu8KvSr3cmGAUSndqxPVgvL5xT/C3S+sABB4H5KGpxlqTmqNn2MWM+oX4HBmsKXzslxIp0tlwqUE4DWaNvCEiKBqEBnWM+QTlSZ5C0kTJl+Os4rfEYC46R0bhHhYxc6NnpNyYv6JwAAAIBktn02O6k+Tg6CwN1RcG+RMZcqwZaUJ/kgDha3Ho9CZCcC5mNiC36M1qGW0J47RoEe5vSAsTitBgyr3pPEZp5+pnJjaXVo3uRWVtsAodDoWG0dOqYEIeX03VqrFQrt3SBsezPrpKoxZgItSbR6XnkK42iSrgk/f6Eyd3ckbh5a7Q== root@tc_239_235'''


        command = "mkdir -p /root/.ssh && echo \"%s\" > /root/.ssh/authorized_keys && chmod 644 /root/.ssh/authorized_keys" % BIZOP_KEY
   
        result,error = self.ssh_con.do_remote_by_passwd_exec(command)

        if result == "wrong":
            logger.write_log("%s 添加key BIZOP_KEY 失败." % host_ip)
        else:
            logger.write_log("%s 添加key BIZOP_KEY 成功." % host_ip)

        command = "echo %s >> /root/.ssh/authorized_keys" % OP_KEY
        result,error = self.ssh_con.do_remote_by_passwd_exec(command)

        if result == "wrong":
            logger.write_log("%s 添加key OP_KEY 失败." % host_ip)
        else:
            logger.write_log("%s 添加key OP_KEY 成功." % host_ip)

    def add_hostname(self,host_ip):
        '''
            添加hostname 清理原有hostname
        '''

        inner_domain = "sogou-in.domain"
        look_hosts_cmd = "cat /etc/hosts"
        look_network_cmd = "cat /etc/sysconfig/network"
        short_host_name = ""
        hostname_list = []

        if common_lib.get_idc_name(host_ip.strip()):
            idcname,host_busi_ip,host_data_ip = common_lib.get_idc_name(host_ip)
        else:
            logger.write_log("host: %s,get_idc_name failed." % host_ip)
            return False

        #hostname信息
        result,error = self.ssh_con.do_remote_by_passwd_exec(look_network_cmd)

        if result == "wrong":
            logger.write_log("host: %s,get host info failed.Detail: %s" % host_ip,error)
            return False


        buf = StringIO.StringIO(result)
        for line in buf.readlines():
            line = line.strip()
            if line.startswith("HOSTNAME"):
                short_host_name = line.split("=")[1]
        
        hostname = short_host_name + "." + inner_domain
        p1 = re.compile("(.*)%s()"  % short_host_name)
        #hostname信息
        result,error = self.ssh_con.do_remote_by_passwd_exec(look_hosts_cmd)

        if result == "wrong":
            logger.write_log("host: %s,get host info failed.Detail: %s" % host_ip,error)
            return False

        buf = StringIO.StringIO(result)
        for line in buf.readlines():
            line = line.strip()
            if p1.match(line):
                delete_old_cmd = "sed -i /%s/d /etc/hosts" % short_host_name
                self.ssh_con.do_remote_by_passwd_exec(delete_old_cmd)
        #添加hostname
        add_hostname = "%s   %s   %s" %  (host_data_ip,hostname,short_host_name)
        add_hostname_cmd = "echo -e \"%s\" >> /etc/hosts" % add_hostname

        self.ssh_con.do_remote_by_passwd_exec(add_hostname_cmd)

        return hostname 

    def clean_ca_cert(self,remote_hostname,ca_info):
        '''
            清理CA证书
        '''
        clean_cmd_all = ""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ca_host  = ca_info['ca_host_ip']
        ca_user  = ca_info['ca_host_user']
        ca_pass  = ca_info['ca_host_password']
        

        clean_cmd = "puppet cert -c %s;" % remote_hostname
        clean_cmd_all += clean_cmd

        try:
            ssh.connect(hostname = ca_host, username = ca_user, password=ca_pass)
            stdin,stdout,stderr = ssh.exec_command(clean_cmd_all)
            result = stdout.read()
            error  = stderr.read()
        except Exception,e:
            logger.write_log("host: %s,%s" % (host,e))
            return False
        else:
            return True
    

    def trans_file(self,host,client_port,default_user,default_client_password,src,dst):
        '''
            传输文件
        '''
        transport = paramiko.Transport(host,client_port)
        transport.connect(username = default_user, password=default_client_password)
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


    def install_soft_programe(self,host_ip,remote_info):
        '''
            安装软件
        '''
        client_port = int(remote_info['client_port'])
        default_user = remote_info['client_user']
        default_client_password = remote_info['client_password']

        scripts_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts')
        src_file = "%s/%s" % (scripts_dir,"init_env.sh")
        
        dst_file = "/usr/local/src/init_env.sh"
       
        self.trans_file(host_ip,client_port,default_user,default_client_password,src_file,dst_file)

        cmd_remote = "bash %s" % (dst_file)

        result,error = self.ssh_con.do_remote_by_passwd_exec(cmd_remote)
        if result == "wrong":
            logger.write_log("host: %s,Install Soft failed." % host_ip) 
        else:
            logger.write_log("host: %s finish soft install" % host_ip)
        


    def get_system_release(self):
        '''
            获取操作系统版本
        '''

        string = ""
        _command = 'cat /etc/issue'

        result,error = self.ssh_con.do_remote_by_passwd_exec(_command)

        for i in result.split(" "):
            if i == "(Santiago)\nKernel":
                continue
            elif i == "on":
                continue
            elif i == "an":
                continue
            else:
                string = string + " " + i.strip("\n").strip("\r").strip("\m")
        return  string


    def get_system_hostname(self,host_ip):
        '''
            获取服务器主机hostname
        '''
        string = ""
        _command = 'hostname -f'

        result,error = self.ssh_con.do_remote_by_passwd_exec(_command)

        if result == "wrong":
            logger.write_log("host: %s 获取hostname 失败." % host_ip)
        else:
            logger.write_log("host: %s 获取hostname 成功." % host_ip)
        return  result

    def get_adapter_mac(self):
        '''
            获取服务器物理网卡地址
        '''
        eth0_mac,eth1_mac,eth2_mac,eth3_mac = "","","",""
        temp_list = {}
        
        begin = re.compile("(.*)(eth[0-9])(.*)")
        end = re.compile("(.*)link/ether\s(\S*)")
        string = ""
        _command = 'ip link'

        result,error = self.ssh_con.do_remote_by_passwd_exec(_command)

        if result == "wrong":
            return False
        else:
            new_block = False
            for line in result.split("\n"):
                if new_block:
                    if end.match(line):
                        adapter_mac = end.match(line).group(2)
                        temp_list[adapter_name] = adapter_mac
                        new_block = False
                else:
                    if begin.match(line):
                        adapter_name = begin.match(line).group(2)
                        new_block = True

                
        for key,value  in temp_list.items():
            if key == "eth0":
                eth0_mac = value
            elif key == "eth1":
                eth1_mac = value
            elif key == "eth2":
                eth2_mac = value
            elif key == "eth3":
                eth3_mac = value

        return eth0_mac,eth1_mac,eth2_mac,eth3_mac

    def get_system_product(self):
        '''
            获取服务器主机序列号和生产商
        '''
        
        _command = 'dmidecode -t system'

        result,error = self.ssh_con.do_remote_by_passwd_exec(_command)

        if result == "wrong":
            return False
        else:
            for line in result.split("\n"):
                line = line.strip()
                if line.startswith("Manufacturer:"):
                    server_manufacturer = line.split(":")[1]
                elif line.startswith("Serial Number:"):
                    server_sn  = line.split(":")[1]
                elif line.startswith("Product Name:"):
                    product_name = line.split(":")[1]
        return  server_manufacturer,server_sn,product_name

    def judge_cloud_type(self,server_package):
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


    def get_server_info(self,host_ip,server_package,client_info,machine_type):
        '''
            保存机器信息
        '''
        relase,hostname,idcname,host_busi_ip,host_data_ip = "","","","",""
        eth0_mac,eth1_mac,eth2_mac,eth3_mac = "","","",""
        server_manufacturer,server_sn,product_name = "","",""

       
        relase = self.get_system_release()
        hostname = self.get_system_hostname(host_ip)

        if common_lib.get_idc_name(host_ip):
            idcname,host_busi_ip,host_data_ip = common_lib.get_idc_name(host_ip)
        else:
            logger.write_log("get_idc_name failed.")
        
        if self.get_adapter_mac():
            eth0_mac,eth1_mac,eth2_mac,eth3_mac = self.get_adapter_mac()
        else:
            logger.write_log("get_adapter_mac failed.")

        if self.get_system_product():
            server_manufacturer,server_sn,product_name = self.get_system_product()
        else:
            logger.write_log("get_system_product failed.")

        temp_dic = {}
        temp_dic['client_hostname'] = hostname.strip("\n")
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
        temp_dic['cloud_type'] = self.judge_cloud_type(server_package)
        temp_dic['machine_type'] = machine_type
        temp_dic['client_user'] = client_info['client_user']

        self.save_server_info(temp_dic)

    def save_server_info(self,client_info):
        '''
            保存服务器状态信息
        '''
        server_type  = client_info['machine_type']
        new_password = ""
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
        modify_date =  time.strftime("%Y-%m-%d",time.localtime())
        cloud_type = client_info['cloud_type']
        

        sql = "select `id` from server_info where host_busi_ip = '%s' and server_sn = '%s'" 

        result = super(Control_key,self).select_advanced(sql,host_busi_ip,server_sn)

        if len(result) > 0:
            for sn in result:
                    conditional_query_two = 'id = %s '
                    super(Control_key,self).update('server_info', conditional_query_two,sn,host_data_ip=host_data_ip,host_busi_ip=host_busi_ip,host_name=host_name,user_account=user,root_password=new_password,server_release=relase,server_type=server_type,cloud_type=cloud_type,server_manufacturer=server_manufacturer,server_sn=server_sn,product_name=product_name,eth0_mac=eth0_mac,eth1_mac=eth1_mac,eth2_mac=eth2_mac,eth3_mac=eth3_mac,idc_name=idc_name,modify_date=modify_date)

        else:
            super(Control_key,self).insert('server_info',host_data_ip=host_data_ip,host_busi_ip=host_busi_ip,host_name=host_name,user_account=user,root_password=new_password,server_release=relase,server_type=server_type,cloud_type=cloud_type,server_manufacturer=server_manufacturer,server_sn=server_sn,product_name=product_name,eth0_mac=eth0_mac,eth1_mac=eth1_mac,eth2_mac=eth2_mac,eth3_mac=eth3_mac,idc_name=idc_name,modify_date=modify_date)  

        client_info = {}