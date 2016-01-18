#!/usr/bin/python
# -*- coding: utf-8 -*-


import deal_ssh,common_lib
import StringIO
import re,sys,time,logger
from mylib.base import Init_Base

import pprint

class Deal_machine_status(Init_Base):
    '''
        处理服务进程状态类
    '''
    def __init__(self,db_server_info,host_ip,ssh_con):
        super(Deal_machine_status, self).__init__(db_server_info)
        self.host_ip = host_ip
        self.ssh_con = ssh_con

    def check_machine_status(self):
        '''
            查询数据库，未分配的服务器
        '''
        sql = "select server_status from server_info where host_data_ip = '%s' or host_busi_ip = '%s'" 
        result_id = super(Deal_machine_status, self).select_advanced(sql,self.host_ip,self.host_ip)
        
        if len(result_id) == 0:
            return True

        if result_id[0] == None:
            return True

        if len(result_id) > 0:
            if int(result_id[0]) == 1:
                logger.write_log("Machine: %s has used! Please check it!" % self.host_ip)
                return False
            else:
                return True
        else:
            return True

    def get_machine_status(self):
        '''
            获取服务器进程，无任何进程即可安装机器
        '''

        dangerous_list = []
        server_list = {}
        import re
        port = re.compile("(.*):(80|8080|3306|1521)(.*)")
        process = re.compile("(.*)(httpd|mysql|nginx|java|oracle)(.*)")
        process_cmd = "netstat -tnpl" 

        result_id = ""

        result,error = self.ssh_con.do_remote_by_passwd_exec(process_cmd)
        if result == "wrong":
            logger.write_log("host: %s . get host info failed." % self.host_ip)

        buf = StringIO.StringIO(result)
        for line in buf.readlines():
            line = line.strip()
            if line.startswith("Proto"):
                continue
            elif process.match(line):
                dangerous_process = process.match(line).group(2)
                dangerous_list.append(dangerous_process)

        server_list[self.host_ip] = dangerous_list
        return server_list


    def set_machine_status(self,server_list):
        '''
            设置服务器状态
            0:待分配
            1:已分配
            2:待处理
        '''
        for server_ip,server_data in server_list.items():
            sql = "select id from server_info where host_data_ip = '%s' or host_busi_ip = '%s' "
            result_id = super(Deal_machine_status, self).select_advanced(sql,server_ip,server_ip)
            if len(result_id) > 0:
                    if len(server_data) > 0: 
                        sql = "update server_info set server_status = 2 where id = '%s'"
                        super(Deal_machine_status,self).update_advanced(sql,result_id[0])
                    else:
                        sql = "update server_info set server_status = 0 where id = '%s'"
                        super(Deal_machine_status,self).update_advanced(sql,result_id[0])
                
    def finish_machine_status(self):
        '''
            结束服务器状态
        '''
        sql = "select id from server_info where host_data_ip = '%s' or host_busi_ip = '%s' "
        result_id = super(Deal_machine_status, self).select_advanced(sql,self.host_ip,self.host_ip)
        if len(result_id) > 0:
            sql = "update server_info set server_status = 2 where id = '%s'"
            super(Deal_machine_status,self).update_advanced(sql,int(result_id[0]))
                



