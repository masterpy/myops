#!/usr/bin/python
# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
import os,subprocess
from IPy import IP
import deal_ssh
import re
import shlex

class Get_conf(ConfigParser):
    def __init__(self,config):
        ConfigParser.__init__(self)
        self.config  = config

    def get_value(self):
        '''
            读取配置文件
            tag: client_server or db_server
        '''
        args,args1 ={},{}
        self.read(self.config)
        for key in self.sections(): 
            options = self.options(key)
            for values in options:
                args[values] = self.get(key,values)
            args1[key] = args 
            args = {}
        return args1



def get_remote_server_info(filename):
    '''
        获取 machine.conf 配置信息
    '''
    conf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir,"config")) 
    if len(conf_dir) == 0:
        conf_dir = "."
    conf_file = "%s/%s" % (conf_dir,filename)
    conf = Get_conf(conf_file)
    conf_info = conf.get_value()
    return conf_info


def ipFormatChk(self,ip_str):
    '''
        ip合法性检查
    '''
    pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"

    if re.match(pattern, ip_str):
        return True
    else:
        return False


def get_idc_name(real_ip):
    '''
        返回业务网地址和数据网地址以及返回idc名字
    '''
    

    iplists = [{'name':'石景山联通机房','data_ip':'10.134','busi_ip':'10.144'},
                {'name':'土城联通机房_网段一','data_ip':'10.11','busi_ip':'10.13'},
                {'name':'土城联通机房_网段二','data_ip':'10.137','busi_ip':'10.147'},
                {'name':'永丰电信机房','data_ip':'10.139','busi_ip':'10.149'},
                {'name':'大郊亭电信机房','data_ip':'10.12','busi_ip':'10.14'},
                {'name':'新兆维电信机房','data_ip':'10.136','busi_ip':'10.146'},
                {'name':'新兆维电信机房','data_ip':'10.142','busi_ip':'10.152'}]

    if len(real_ip) == 0:
        return False

    real_ip_net = ".".join(IP(real_ip).strNormal().split('.')[:-2])
    real_ip_addr = ".".join(IP(real_ip).strNormal().split('.')[2:])

    for pool in iplists:
        if str(pool['busi_ip']) == str(real_ip_net):
            idcname = pool['name']
            busi_ip = pool['busi_ip'] + "." + real_ip_addr
            data_ip = pool['data_ip'] + "." + real_ip_addr

        elif str(pool['data_ip']) == str(real_ip_net):
            idcname = pool['name']
            busi_ip = pool['busi_ip'] + "." + real_ip_addr
            data_ip = pool['data_ip'] + "." + real_ip_addr

    return idcname,busi_ip,data_ip


def get_system_release(host_info):
    '''
        获取操作系统版本
    '''

    string = ""

    _command = 'cat /etc/issue'

    result,error = deal_ssh.remote_ssh_key_exec(host_info,_command)

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


def get_system_hostname(host_info):
    '''
        获取服务器主机hostname
    '''
    
    string = ""

    _command = 'hostname -f'

    result,error = deal_ssh.remote_ssh_key_exec(host_info,_command)

    if result == "wrong":
        print "host: %s 获取hostname 失败." % host_info['client_server']['client_ip']
    else:
        print "host: %s 获取hostname 成功." % host_info['client_server']['client_ip']

    return  result

def get_adapter_mac(host_info):
    '''
        获取服务器物理网卡地址
    '''
    eth0_mac,eth1_mac,eth2_mac,eth3_mac = "","","",""
    temp_list = {}
    
    begin = re.compile("(.*)(eth[0-9])(.*)")
    end = re.compile("(.*)link/ether\s(\S*)")
    string = ""
    _command = 'ip link'

    
    result,error = deal_ssh.remote_ssh_key_exec(host_info,_command)

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

def get_system_product(host_info):
    '''
        获取服务器主机序列号和生产商
    '''
    
    _command = 'dmidecode -t system'

    result,error = deal_ssh.remote_ssh_key_exec(host_info,_command)

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


def install_soft_programe(host_ip_list,machine_info):
    '''
        安装软件
    '''
    remote_user = machine_info['client_user']
    remote_passwd = machine_info['client_password']
    remote_port = machine_info['client_port']

    scripts_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0],'scripts')
    src_file = "%s/%s" % (scripts_dir,"init_env.sh")
    
    dst_file = "/usr/local/src/init_env.sh"
   
    for host_ip in  host_ip_list:
        deal_ssh.trans_file(host_ip,remote_user,remote_passwd,src_file,dst_file)
        cmd_remote = "bash %s" % (dst_file)
        result  = deal_ssh.remote_ssh_password_simple_online(host_ip,remote_user,remote_passwd,cmd_remote)
        if isinstance(result,bool):
            return False
        else:
            print "host: %s finish soft install" % host_ip
    
    return True



