#!/usr/bin/python
# -*- coding: utf-8 -*-

from mysql_cls import MysqlPython
import deal_ssh,common_lib
import StringIO
import re,sys,time
from mylib.base import Init_Base
import math


class Memory_cls(Init_Base):
    '''
        处理内存信息类
    '''
    def __init__(self,init_server_info,db_server_info):
        super(Memory_cls, self).__init__(init_server_info,db_server_info)


    def get_vm_memory_info(self):
        '''
            获取虚机内存相关数据
        '''
        cmd = "free -m |grep \"Mem\" | awk '{print $2}'"
        templist = []

        for server_info in self.init_server_info: 
            host_ip = server_info['client_server']['client_ip']
            #分区信息
            result,error = deal_ssh.remote_ssh_key_exec(server_info,cmd)
            memory_size = result.strip()
            
            memory_info = {"memory_size":math.ceil(float(memory_size)/1024.000),"memory_type":"NULL","memory_speed":"NULL"}
            templist.append(memory_info)
            memory_info = {}


            if self.save_memory_info(host_ip,templist):
                print "host: %s save_memory_info success!" %  host_ip
            else:
                print "host: %s save_memory_info failed!"  % host_ip

            templist = []
        

    def get_machine_memory_info(self):
        '''
            获取实体机内存相关数据
        '''
        cmd = "test -e /usr/sbin/dmidecode && dmidecode -t memory"

        memory_begin = re.compile("^Memory Device")
        memory_end = re.compile("^Configured Clock Speed")
        new_block  = False
        memory_info = {}
        host_info = {}
        templist    = []
        has_speed = True

        memory_size = "NULL"
        memory_type = "NULL"
        memory_speed = "NULL"

        for server_info in self.init_server_info: 
            host_ip = server_info['client_server']['client_ip']
            
            #分区信息
            result,error = deal_ssh.remote_ssh_key_exec(server_info,cmd)

            if result == "wrong":
                print "host: %s . read lvm info failed." %  server_info['c778lient_server']['client_ip']
                continue

            buf = StringIO.StringIO(result)
            for line in buf.readlines():
                line = line.strip()
                if new_block:
                    if memory_end.match(line):
                        memory_info = {"memory_size":memory_size,"memory_type":memory_type,"memory_speed":memory_speed}
                        templist.append(memory_info)
                        memory_info = {}

                    else:
                        if line.startswith("Size"):
                            temp = line.split()[1]
                            if temp == "No":
                                memory_size = "NULL"
                            else:
                                memory_size = int(temp)/1024

                        elif line.startswith("Type:"):
                            p = re.compile("(.*)OUT(.*)")
                            if p.match(line):
                                memory_type = "NULL"
                            else:
                                memory_type = line.split()[1]

                        # elif line.startswith("Part Number"):
                        #     q = re.compile("(.*)NO DIMM(.*)")
                        #     if q.match(line):
                        #         has_speed = False
                        #     else:
                        #         has_speed = True

                        elif line.startswith("Speed:"):
                            if line.split()[1] == "Unknown":
                                memory_speed = "NULL"
                            else:
                                memory_speed = line.split()[1] + "MHz"


                else:
                    if memory_begin.match(line):
                        new_block = True


            if self.save_memory_info(host_ip,templist):
                print "host: %s save_memory_info success!" % host_ip
            else:
                print "host: %s save_memory_info failed!" % host_ip

            templist = []

    def save_memory_info(self,host_ip,memoryinfo):

        sql = "select `id`,`host_busi_ip` from server_info where host_data_ip = '%s' or host_busi_ip = '%s'"
        result  =  super(Memory_cls,self).select_advanced(sql,host_ip,host_ip)

        if len(result) > 0:
            server_id = result[0][0]
            server_busi_ip = result[0][1] 
        else:
            server_id = -1 
        
        #先清理表
        sql  = "delete from memory_info where server_busi_ip = '%s'"
        super(Memory_cls,self).delete(sql,server_busi_ip) 
        sum_size = 0
        for data in memoryinfo:
            if data['memory_size'] == "NULL":
                pass
            else:
                sum_size += int(data['memory_size'])

            sql = "insert into memory_info (server_id,server_busi_ip,mem_size,mem_type,mem_speed) values (%s,'%s','%s','%s','%s');"
            
            insert_id = super(Memory_cls,self).insert_advanced(sql,server_id,server_busi_ip,data['memory_size'],data['memory_type'],data['memory_speed'])
            
            if insert_id > 0:
                pass

            else:
                print "update table memory_info failed!"
                return False


        memory = str(sum_size) + "G"
        sql = "update server_info set memory_size = '%s' where id = '%s' and host_busi_ip = '%s'"
        super(Memory_cls,self).update_advanced(sql,memory,server_id,server_busi_ip)
        return True


