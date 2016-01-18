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
        logger.write_log("host: %s network is down,please check it!" % ip)
        return False
    return True



def do_init_info(source_filename):
    '''
        收集信息和安装软件
    '''
    init_server_info = {}
    tempdic,tempdic2 = {},{}

    iplist = [] #ip列表
    pmlist = [] #实体机列表
    vmlist = [] #虚机列表

    if len(source_filename) == 0:
        return 
    else:
        filename = source_filename


    init_server_info = common_lib.get_remote_server_info('init.conf')
    tempdic = init_server_info['client_server'].copy()
    
    
    with open(filename,'r') as f:
        for line in f.readlines():
            tempdic['group'] = line.split()[4]
            tempdic['use_default_raid'] = line.split()[3]
            tempdic['server_package'] = line.split()[2]
            tempdic['machine_type'] = line.split()[1]
            tempdic['client_ip'] = line.split()[0]
            
            #############################################################
            #############################################################
            #step 1 检查网络，安装软件，添加hostname,添加信任关系
            #############################################################
            #############################################################
            #检查网络
            if not check_network(tempdic['client_ip']):
                continue
            #初始化ssh类
            ssh_cls = deal_ssh.Ssh_Cls(tempdic['client_ip'])

            process_cls = deal_machine_status.Deal_machine_status(init_server_info['db_server'],tempdic['client_ip'],ssh_cls)
            #检查进程
            if not process_cls.check_machine_status():
                continue

            #添加root key,非数据库机器
            if tempdic['group'] != "db":
                control_key_cls = deal_key_server_info.Control_key(init_server_info['db_server'],ssh_cls)
                control_key_cls.control_key(tempdic['client_ip'])

            #添加hostname
            hostname = control_key_cls.add_hostname(tempdic['client_ip'])
            #清理CA
            control_key_cls.clean_ca_cert(hostname,init_server_info['ca_server'])
            #安装软件
            control_key_cls.install_soft_programe(tempdic['client_ip'],init_server_info['client_server'])
            
            #############################################################
            #############################################################
            #step 2 保存分区信息和磁盘信息，以及机器信息
            #############################################################
            #############################################################
            #保存机器基本信息
            control_key_cls.get_server_info(tempdic['client_ip'],tempdic['server_package'],init_server_info['client_server'],tempdic['machine_type'].lower())

            #保存分区信息和磁盘信息,虚机和实机处理方式不一样
            if tempdic['machine_type'].lower() == "pm":
                deal_raid_cls = deal_disk_raid.Deal_Raid_info(init_server_info['db_server'],tempdic['client_ip'],ssh_cls)
                deal_raid_cls.get_disk_info()
                set_disk_info = deal_pm_disk_info.Deal_Pm_Disk_Info(init_server_info['db_server'])
                set_disk_info.update_pm_info(tempdic['client_ip'],tempdic['server_package'])
                
            
            #处理分区信息
            partition_cls = deal_partition.Parted_Disk_init(init_server_info['db_server'],tempdic['client_ip'],ssh_cls)
            partition_data = partition_cls.get_init_partition_info()
            partition_cls.save_partition_info(partition_data)
            #处理ted 分区信息
            partition_cls.get_search_ted_info()

            #保存内存信息
            memory_cls = deal_memory.Memory_cls(init_server_info['db_server'],tempdic['client_ip'],ssh_cls)

            if tempdic['machine_type'].lower() == "vm":
                memory_cls.get_vm_memory_info()

            elif tempdic['machine_type'].lower() == "pm":
                memory_cls.get_machine_memory_info()

            #更新主机状态
            
            data = ""
            data = process_cls.get_machine_status()
            #保存主机状态
            process_cls.set_machine_status(data)
            process_cls.finish_machine_status()

            #############################################################
            #############################################################
            #step 3  自动分区和自动挂载
            #############################################################
            #############################################################
            
            partion_disk_cls = deal_partition.Exec_partition_cls(init_server_info['db_server'],tempdic['client_ip'],ssh_cls)

            if tempdic['machine_type'].lower() == "pm":
                deal_raid_cls.set_disk_info(tempdic['use_default_raid'],tempdic['server_package'])
                partion_disk_cls.set_pm_partition_info(tempdic['server_package'])

                partition_data = partition_cls.get_init_partition_info()
                partition_cls.save_partition_info(partition_data)

            elif tempdic['machine_type'].lower() == "vm":
                partion_disk_cls.set_vm_partition_info()


            #############################################################
            #############################################################
            #step 4  修改服务器密码
            #############################################################
            #############################################################
            newpass_cls =  deal_gernal_password.PassWorder(init_server_info['db_server'],ssh_cls)
            newpass = newpass_cls.gernal_password()
            encrypt_pass = newpass_cls.encrypt_password(newpass)
            newpass_cls.save_password(tempdic['client_ip'],newpass,encrypt_pass)



def main(tag,source_filename=""):
    do_init_info(source_filename)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Init machine')
    parser.add_argument('-o', action="store", dest="action",help="操作机器 -o init 初始化")
    parser.add_argument('-f', action="store", dest="filename",help="-f 指定配置文件,默认/tmp/machine.list")
    results = parser.parse_args()

    if not results.filename:
        source_filename = "/tmp/machine.list"
    else:
        source_filename = results.filename

    if results.action == "init":
        main("init",source_filename)
    else:
        parser.print_help()