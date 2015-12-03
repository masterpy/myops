#!/usr/bin/python
# -*- coding: utf-8 -*-
import deal_ssh,common_lib
import StringIO
from base import Init_Base
import MySQLdb


class Machine_status_cls(Init_Base):
    def __init__(self,init_server_info,db_server_info):
        super(Machine_status_cls, self).__init__(init_server_info,db_server_info)
    
    def get_login_data(self,ip):
        '''
            获取登录信息
        '''
        import re

        result = True
        Jul_Count,Jun_Count,May_Count = 0,0,0
        user = "for_monitor"

        get_julcmd = "sudo last -t 2015073100000 > ~/x1.txt;sudo last -t 2015070100000 >> ~/x1.txt;cat ~/x1.txt | sort  | uniq -c | sort -nr | grep \"Jul\"  | wc -l"

        get_juncmd = "sudo last -t 2015063000000 > ~/x2.txt;sudo last -t 2015060100000 >> ~/x2.txt;cat ~/x2.txt | sort  | uniq -c | sort -nr | grep \"Jun\"  | wc -l"

        get_maycmd = "sudo last -t 2015053100000 > ~/x3.txt;sudo last -t 2015050100000 >> ~/x3.txt;cat ~/x3.txt | sort  | uniq -c | sort -nr | grep \"May\"  | wc -l"

    
        Jul_Count = deal_ssh.remote_ssh_key_exec_simple(ip,user,get_julcmd)
        if not Jul_Count:
            f = open("error_host",'a+')
            f.write("Can't connect host:%s\n" % ip)
            f.close()
            return False

        if len(Jul_Count) > 0:
            Jun_Count = deal_ssh.remote_ssh_key_exec_simple(ip,user,get_juncmd)
            if len(Jun_Count) > 0:
                May_Count = deal_ssh.remote_ssh_key_exec_simple(ip,user,get_maycmd)

        sql = "select id from server_use_info where server_ip = '%s'"
                
        result = super(Machine_status_cls, self).select_advanced(sql,ip)
    
        if len(result) > 0:
            sql = "update server_use_info set Jul_login_Count = %s, Jun_login_Count = %s,May_login_Count = %s where server_ip = '%s' "
            super(Machine_status_cls,self).update_advanced(sql,Jul_Count,Jun_Count,May_Count,ip)
        else:
            sql = "insert into server_use_info (server_ip,Jul_login_Count,Jun_login_Count,May_login_Count) values ('%s',%s,%s,%s);"
            super(Machine_status_cls,self).insert_advanced(sql,ip,int(Jul_Count),int(Jun_Count),int(May_Count))

        return True




    def get_cron_data(self,ip):
        '''
            获取crontab 任务数量
        '''
        temp_dic,temp_dic2 = {},{}
        remote_user = "for_monitor"
        get_user_cmd = "sudo ls /var/spool/cron/"

        result = deal_ssh.remote_ssh_key_exec_simple(ip,remote_user,get_user_cmd)

        if result:
            buf = StringIO.StringIO(result)
            for user in buf.readlines():       
                user = user.strip()      
                if user == "root":
                    get_cront_root_content_cmd = "sudo sed '/^$/d' /var/spool/cron/%s | grep -v \"clock\" | wc -l" % user
                    result = deal_ssh.remote_ssh_key_exec_simple(ip,remote_user,get_cront_root_content_cmd)
                    temp_dic[user] = result.strip()
                else:
                    get_cront_root_other_cmd   = "sudo sed '/^$/d' /var/spool/cron/%s | wc -l " % user
                    result = deal_ssh.remote_ssh_key_exec_simple(ip,remote_user,get_cront_root_other_cmd)
                    temp_dic[user] = result.strip()    
                        
            temp_dic2[ip] = temp_dic    

        return temp_dic2

    def check_process(self,ip):
        '''
            检查服务器进程
        '''
        dangerous_list = []
        temp_dic = {}
        import re
        #port = re.compile("(.*):(80|8080|3306|1521)(.*)")
        process = re.compile("(.*)(httpd|mysqld|nginx|java|oracle)(.*)")
        remote_user = "for_monitor"
        process_cmd = "sudo netstat -tnpl" 
        
        result = deal_ssh.remote_ssh_key_exec_simple(ip,remote_user,process_cmd)
        if result:
            buf = StringIO.StringIO(result)
            for line in buf.readlines():
                line = line.strip()
                if line.startswith("Proto"):
                    continue
                elif process.match(line):
                    dangerous_process = process.match(line).group(2)
                    dangerous_list.append(dangerous_process)

            temp_dic[ip] = dangerous_list

        return  temp_dic   

   

    def save_cron_data(self,result_dic):
        '''
            保存cron 数据
        '''
        Root_count = 0
        Other_count = 0
        for key,value in result_dic.items():
            for user,count in value.items():
                if user == "root":
                    Root_count = count
                else:
                    Other_count = count 

            sql = "update server_use_info set cron_other = '%s' , cron_root = '%s' where server_ip = '%s' "
            super(Machine_status_cls,self).update_advanced(sql,int(Other_count),int(Root_count),key)

    def save_sevice_dec(self,result_dic):
        '''
            保存服务名称
        '''
        temp = []
        service_desc = ""
        content = ""
        for key,value in result_dic.items():
            for service in value:
                if service not in  temp:
                    temp.append(service)
                    content += service + ","

            sql = "update server_use_info set service_desc = '%s' where server_ip = '%s' "
            
            super(Machine_status_cls,self).update_advanced(sql,content,key)



if __name__ == '__main__':
    db_info = {'db_host_ip': '10.149.45.69', 'db_host_user': 'user_account', 'db_host_password': 'user_pass', 'db_host_port': '3306', 'db_dbname': 'user_db'}

    result_dic1,result_dic2,result_dic4 = {},{},{}

    user  = "root"
    #machine_file = "/tmp/test.machine"
    machine_file = "/tmp/1"
    machine_cls = Machine_status_cls(db_info,db_info)

    with open(machine_file,'r') as f:
        for line in f.readlines():
            ip = line.strip().strip("\n")

            result_dic1 =  machine_cls.get_login_data(ip)
            if result_dic1:
                result_dic2 = machine_cls.get_cron_data(ip)
                machine_cls.save_cron_data(result_dic2)
                result_dic3 = machine_cls.check_process(ip)
                machine_cls.save_sevice_dec(result_dic3)


    