#!/usr/bin/python
# -*- coding: utf-8 -*-

import pprint
import sys
from  mylib import *
import argparse


def clean_relation_ship(machine_data):
    '''
        清理信任
    '''
    if len(machine_data) > 0:
        for machine in machine_data:
            team = machine['client_server']['group']
            if team == 'online_db' or team == 'online_404':
                deal_password.del_relation_server(machine)
            else:
                return 

def check_network(ip):
    '''
        检查网络
    '''
    tempdic = deal_network.verbose_ping(ip)
   
    if not tempdic:
        print "host: %s network is down,please check it!" %  ip
        return False
    return True


def init_machine_info(machine_ip_list):
    '''
        添加hostname,安装puppet客户端软件
    '''
    init_server_info = common_lib.get_remote_server_info('init.conf')
    #添加hostname
    tools_cls = deal_other.Tools_cls(machine_ip_list,init_server_info['ca_server'],init_server_info['client_server'])
    hostname_list = tools_cls.add_hostname()
    if isinstance(hostname_list,bool):
        print "add hostname failed."
    else:
        #清理ca证书
        tools_cls.clean_ca_cert(hostname_list)
        #安装软件
        if not common_lib.install_soft_programe(machine_ip_list,init_server_info['client_server']):
            print "install soft failed."


def init(machine_data,db_data):
    '''
        初始化
    '''
    #初始化，修改密码，保存密码以及服务器相关信息
    passwd_cls = deal_password.Control_key(machine_data,db_data)
    passwd_cls.add_relation_server()    
    passwd_cls.set_server_status()


def check_process(machine_data,db_data):
    '''
        检查主机进程
    '''
    data = ""
    process_cls = deal_machine_status.Deal_machine_status(machine_data,db_data)
    data = process_cls.get_machine_status()
    #保存主机状态
    process_cls.set_machine_status(data)

def set_memory(machine_data,db_data,tag):
    '''
        獲取內存信息
    '''
    memory_cls = deal_memory.Memory_cls(machine_data,db_data)
    
    if tag == "vm":
        memory_cls.get_vm_memory_info()
    elif tag == "pm":
        memory_cls.get_machine_memory_info()

def get_disk_info(machine_data,db_data):
    '''
        检查硬盘信息，保存硬盘信息
    '''    
    raw_disk_cls = deal_disk_raid.Deal_Raid_info(machine_data,db_data)
    raw_disk_cls.get_disk_info()

    set_disk_info = deal_pm_disk_info.Deal_Pm_Disk_Info(machine_data,db_data)
    set_disk_info.update_pm_info()


def check_partion_info(machine_data,db_data):
    partition_cls = deal_partition.Parted_Disk_init(machine_data,db_data)
    partition_data = partition_cls.get_init_partition_info()
    partition_cls.save_partition_info(partition_data)

def get_partition_info(machine_data,db_data):
    '''
        检查分区信息,保存分区信息
    '''
    partition_cls = deal_partition.Parted_Disk_init(machine_data,db_data)
    partition_data = partition_cls.get_init_partition_info()
    partition_cls.save_partition_info(partition_data)
    partition_cls.get_search_ted_info()


def set_puppet_config(machine_data,db_data,puppet_data):
    '''
        生成puppet配置
    '''
    web_puppet_conf,default_puppet_conf = "",""

    puppet_cls = deal_gerenal_config.Genenal_Puppet_config(machine_data,db_data)

    web_puppet_conf,default_puppet_conf = puppet_cls.genenal_host_config()
    puppet_cls.set_host_config(web_puppet_conf,default_puppet_conf,puppet_data)


def close_puppet_config(puppet_data):
    '''
        关闭puppet配置
    '''
    deal_gerenal_config.close_host_config(puppet_data)


def get_init_info():
    '''
        收集信息和安装软件
    '''
    init_server_info = {}
    tempdic,tempdic2 = {},{}

    iplist = [] #ip列表
    pmlist = [] #实体机列表
    vmlist = [] #虚机列表

    filename = "/tmp/machine.list"


    init_server_info = common_lib.get_remote_server_info('init.conf')
    tempdic = init_server_info['client_server'].copy()
    
    #pmlist可以忽略
    process_cls = deal_machine_status.Deal_machine_status(tempdic,init_server_info['db_server'])

    with open(filename,'r') as f:
        for line in f.readlines():
            tempdic['group'] = line.split()[4]
            tempdic['use_default_raid'] = line.split()[3]
            tempdic['server_package'] = line.split()[2]
            tempdic['machine_type'] = line.split()[1]
            tempdic['client_ip'] = line.split()[0]
            tempdic2['client_server'] = tempdic
            
            #检查网络
            if not check_network(tempdic['client_ip']):
                continue

            if not process_cls.check_machine_status(tempdic['client_ip']):
                continue

            iplist.append(tempdic['client_ip'])

            if tempdic['machine_type'] == "pm":
                pmlist.append(tempdic2)
            elif tempdic['machine_type'] == "vm":
                vmlist.append(tempdic2)
            else:
                print "no exist this machine: %s type!" % tempdic['client_ip']
                sys.exit()

            tempdic = init_server_info['client_server'].copy()
            tempdic2 = {}

    return iplist,pmlist,vmlist

def do_init_info(iplist,pmlist,vmlist):
    
    init_server_info = common_lib.get_remote_server_info('init.conf')
    process_cls = deal_machine_status.Deal_machine_status(pmlist,init_server_info['db_server'])

    if len(pmlist) > 0:
        #初始化实体机
        init(pmlist,init_server_info['db_server'])
        #获取磁盘信息
        get_disk_info(pmlist,init_server_info['db_server'])
        #获取实体机分区信息
        get_partition_info(pmlist,init_server_info['db_server'])
        # #獲取內存信息
        set_memory(pmlist,init_server_info['db_server'],"pm")
        # #检查进程
        check_process(pmlist,init_server_info['db_server'])
        # #更新puppet配置

    elif len(vmlist) > 0:
        pass
        #初始化虚机
        init(vmlist,init_server_info['db_server'])

        #获取虚拟机分区信息
        get_partition_info(vmlist,init_server_info['db_server'])

        #獲取內存信息
        set_memory(vmlist,init_server_info['db_server'],"vm")

        #检查进程
        check_process(vmlist,init_server_info['db_server'])
        
    process_cls.finish_machine_status(iplist)


def set_partition_info(iplist,pmlist,vmlist):
    '''
        设置分区信息
    '''
    host_ok = []
    init_server_info = common_lib.get_remote_server_info('init.conf')

    for ip in iplist:
        if deal_network.verbose_ping(ip):
            host_ok.append(ip)
    
    partion_disk_cls = deal_partition.Exec_partition_cls(host_ok,pmlist,init_server_info['db_server'])
    
    if len(pmlist) > 0:
        raw_disk_cls = deal_disk_raid.Deal_Raid_info(pmlist,init_server_info['db_server'])
        #检查raid并重新划分
        raw_disk_cls.set_disk_info()
        #重新刷新数据库
        #raw_disk_cls.get_disk_info()
        #设置分区信息

        partion_disk_cls.set_pm_partition_info()
        #重新检查分区信息
        check_partion_info(pmlist,init_server_info['db_server'])

    if len(vmlist) > 0: 
        #处理虚机分区信息
        partion_disk_cls.set_vm_partition_info()

  

def main(tag):
    iplist,pmlist,vmlist = "","",""
    iplist,pmlist,vmlist = get_init_info()
    if len(iplist) == 0:
        print "No Machines can be init!"
        return

    if tag == "init":
        init_machine_info(iplist)

    elif tag == "set":
        do_init_info(iplist,pmlist,vmlist)

    elif tag == "do":
        set_partition_info(iplist,pmlist,vmlist)
        clean_relation_ship(pmlist)
        clean_relation_ship(vmlist)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Init machine')
    parser.add_argument('-o', action="store", dest="action",help="操作机器 -o init 初始化 -o do 执行分区操作")
    results = parser.parse_args()
    if results.action == "init":
        main("init")
    elif results.action == "do":
        main("do")
    elif results.action == "set":
        main("set")
    else:
        parser.print_help()