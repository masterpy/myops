#!/usr/bin/python
# -*- coding: utf-8 -*-

import common_lib
import re,sys,time,logger
from mylib.base import Init_Base
import pprint

class Deal_Raid_info(Init_Base):
    '''
        单独处理 raid信息类，依据配置重新配置raid
    '''
    def __init__(self,db_server_info,host_ip,ssh_con):
        super(Deal_Raid_info, self).__init__(db_server_info)
        self.host_ip = host_ip
        self.ssh_con = ssh_con

    def check_tool_file(self):
        '''
            检查硬盘工具是否存在
        '''
        test_filename_command = "test -f /opt/MegaRAID/MegaCli/MegaCli64 && echo \"success\""
    
        result,error = self.ssh_con.do_remote_by_passwd_exec(test_filename_command)
        if result == "wrong":
            logger.write_log("%s %s" % (self.host_ip,error))
            return False
        elif result == "":
            logger.write_log("host:%s MegaCli64 is not exsit." % self.host_ip)
            return False
        else:
            return True 
        
        

    def get_disk_info(self):
        '''
            获取raid盘信息
        '''
        if self.check_tool_file():
            pass
        else:
            return False

        get_raid_info_cmd = "/opt/MegaRAID/MegaCli/MegaCli64 -ldpdinfo -a0  -NoLog"
        self.collect_disk_info(get_raid_info_cmd)


    def collect_disk_info(self,cmd):
        '''
            收集磁盘信息和raid信息
        '''
        raid_info,disk_info = {},{}

        disk_data,raid_data =  [],{}
        
        ld_begin = re.compile("^Virtual Drive")
        ld_end   = re.compile("^Span:")
        pd_begin = re.compile("^PD:")
        pd_end   = re.compile("^Drive has flagged")

        new_pd_block,new_ld_block = False,False
        pd_block,ld_block = '',''
        pd_blocks,ld_blocks = {},{}
        pd_blocks_list,ld_blocks_list = [],[]

        
        result,error = self.ssh_con.do_remote_by_passwd_exec(cmd)
        
        if result == "wrong":
            logger.write_log("host:%s detail:%s" % (self.host_ip,error))
            return False

        if len(result) == 0:
            logger.write_log("host:%s no raid info" % self.host_ip)
            return False
            
        #过滤块信息
        for line in result.split("\n"):
            if ld_begin.match(line):
                key = line.split()[2]

            if new_ld_block:
                if ld_end.match(line):
                    ld_block += line + "\n"
                    ld_blocks_list.append(ld_block)
                    new_ld_block = False
                    ld_block = ''
                else:
                    ld_block += line + "\n"

            else:
                if ld_begin.match(line):
                    new_ld_block = True
                    ld_block += line + "\n"


            if new_pd_block:
                if pd_end.match(line):
                    pd_block += line + "\n"
                    pd_blocks[key] = pd_block
                    pd_blocks_list.append(pd_blocks)
                    new_pd_block = False
                    pd_block = ''
                    pd_blocks = {}
                else:
                    pd_block += line + "\n"

            else:
                if pd_begin.match(line):
                    new_pd_block = True
                    pd_block += line + "\n"

        disk_data,raid_data = self.deal_disk_info(ld_blocks_list,pd_blocks_list)
        ld_blocks_list = []
        pd_blocks_list = []

        if not disk_data:
            logger.write_log("host:%s server collect raid info failed" % self.host_ip)
            return False
        self.update_server_raidinfo(disk_data,raid_data)

    def update_server_raidinfo(self,disk_data,raid_data):
        '''
            更新数据库
        '''

        modify_date =  time.strftime("%Y-%m-%d",time.localtime())
        #更新raid表
        for key,value in raid_data.items(): 
            client_ip = key.split("_")[0]

            virtual_drive_sn = key.split("_")[2]
            raid_name   = value['raid_name']
            raid_size   = value['raid_size']
            disk_num    = value['disk_num']

            sql = "select `id` from server_info where host_busi_ip = '%s'"
            result  =  super(Deal_Raid_info,self).select_advanced(sql,client_ip)
            if len(result) > 0:
                server_id = result[0]
            else:
                server_id = -1 
            
            sql  = "select `server_id` from raid_info where server_busi_ip = '%s' and virtual_drive_sn = '%s'"
            result = super(Deal_Raid_info,self).select_advanced(sql,client_ip,virtual_drive_sn)

            if len(result) > 0:
                sql = "delete from raid_info where server_busi_ip = '%s' and virtual_drive_sn != '%s'"
                super(Deal_Raid_info,self).delete(sql,client_ip,virtual_drive_sn)
                for sn in result:
                    sql = "update raid_info set server_busi_ip = '%s',virtual_drive_sn = '%s',raid_name = '%s',raid_size = '%s',disk_num = '%s',server_id = '%s' where server_busi_ip = '%s' and virtual_drive_sn = '%s'"
                    super(Deal_Raid_info,self).update_advanced(sql,client_ip,virtual_drive_sn,raid_name,raid_size,disk_num,server_id,client_ip,virtual_drive_sn)
            else:
                sql = "insert into raid_info (server_id,server_busi_ip,virtual_drive_sn,raid_name,raid_size,disk_num) values (%s,'%s','%s','%s','%s','%s');"
                super(Deal_Raid_info,self).insert_advanced(sql,server_id,client_ip,virtual_drive_sn,raid_name,raid_size,disk_num)

        #清理diskinfo
        sql = "delete from disk_info where server_busi_ip = '%s'"
        super(Deal_Raid_info,self).delete(sql,client_ip)

        # #更新disk表
        for disk in disk_data:
            client_ip = disk['client_ip']
            disk_sn   = disk['disk_sn']
            disk_type = disk['disk_type']
            disk_size = disk['disk_size']
            disk_status = disk['disk_status']
            slot_number = disk['slot_number']
            media_error = disk['media_error']
            other_error = disk['other_error']
            raid_info   = disk['raid_info']
            virtual_group = disk['virtual_group']

            if disk_type == "SATA" and disk['disk_raw_size'] < 512:
                disk_type = "SSD"

            sql  = "select `disk_id` from disk_info where server_busi_ip = '%s' and disk_sn = '%s'"
            result = super(Deal_Raid_info,self).select_advanced(sql,client_ip,disk_sn)
            if len(result) > 0:
                for sn in result:
                    sql = "update disk_info set server_busi_ip = '%s',virtual_group = '%s',disk_sn = '%s',disk_type = '%s',disk_size = '%s',disk_status = '%s',slot_number = '%s',media_error_count = '%s',other_error_count = '%s',raid_info = '%s',server_id = '%s' where server_busi_ip = '%s' and disk_sn = '%s'"
                    super(Deal_Raid_info,self).update_advanced(sql,client_ip,virtual_group,disk_sn,disk_type,disk_size,disk_status,slot_number,media_error,other_error,raid_info,server_id,client_ip,disk_sn)
            else:
                sql = "insert into disk_info (server_busi_ip,virtual_group,disk_sn,disk_type,disk_size,disk_status,slot_number,media_error_count,other_error_count,raid_info,server_id) values ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');"
                super(Deal_Raid_info,self).insert_advanced(sql,client_ip,virtual_group,disk_sn,disk_type,disk_size,disk_status,slot_number,media_error,other_error,raid_info,server_id)



    def deal_disk_info(self,ld_blocks_list,pd_blocks_list):
        '''
            保存raid和磁盘信息，不做重新raid等处理
        '''
        if len(ld_blocks_list) == 0:
            logger.write_log("host: %s,ld_blocks_list no data" % self.host_ip)
            return False,False

        if len(pd_blocks_list) == 0:
            logger.write_log("host: %s,pd_blocks_list no data" % self.host_ip)
            return False,False


        p1 = re.compile("(.*)Primary-([0-9])(.*)")
        ld_begin = re.compile("^Virtual Drive")

        disk_list = []
        raid_info,disk_info = {},{}

        if common_lib.get_idc_name(self.host_ip.strip()):
            idcname,host_busi_ip,host_data_ip = common_lib.get_idc_name(self.host_ip)
        else:
            logger.write_log("host: %s,get_idc_name failed." % self.host_ip)

        client_ip = host_busi_ip

        for ld_info in ld_blocks_list:
            for line in ld_info.split("\n"):
                if line.startswith("Virtual Drive:"):
                    key =  line.split()[2]
                if p1.match(line):
                    raid_name = 'raid-' + p1.match(line).group(2)
                elif line.startswith("Size"):
                    raid_size = line.split(":")[1]
                elif line.startswith("Number Of Drives"):
                    drives = line.split(":")[1]
                elif line.startswith("Span Depth"):
                    if len(drives) > 0:
                        disk_num = int(drives) * int(line.split(":")[1])
                    if int(line.split(":")[1]) > 1:
                        raid_name = 'raid-10'

            info_key = "%s_vd_%s" % (client_ip,key)
            raid_info[info_key] = {'raid_name':raid_name,'disk_num':disk_num,'raid_size':raid_size}

        #盘组列表
        for pd_info in pd_blocks_list:
            #一块磁盘字典（key为raid相关)
            for key,value in pd_info.items():
                #一个磁盘的详细信息
                for line in value.split("\n"):
                    #raid组信息
                    for raid_key,raid_value in raid_info.items():
                        if int(raid_key.split("_")[2]) == int(key):
                            if line.startswith("WWN"):
                                disk_sn = line.split(":")[1]
                            elif line.startswith("PD Type:"):
                                disk_type = line.split(":")[1]
                            elif line.startswith("Slot Number:"):
                                slot_number = line.split(":")[1]
                            elif line.startswith("Media Error Count:"):
                                media_error = line.split(":")[1]
                            elif line.startswith("Other Error Count:"):
                                other_error = line.split(":")[1]      
                            elif line.startswith("Raw Size:"):
                                disk_size = line.split(":")[1].split()[0]+line.split(":")[1].split()[1]
                                disk_raw_size = int(float(line.split(":")[1].split()[0]))
                            elif line.startswith("Firmware state:"):
                                disk_status = line.split(":")[1].split(",")[0]


                            raid_name = raid_value['raid_name']

                disk_list.append({'client_ip':client_ip,'disk_sn':disk_sn.strip(),'virtual_group':key,'disk_type':disk_type.strip(),'disk_size':disk_size.strip(),'disk_raw_size':disk_raw_size,'disk_status':disk_status.strip(),'slot_number':slot_number.strip(),'media_error':media_error,'other_error':other_error,'raid_info':raid_name.strip()})
                     
        return disk_list,raid_info
    

    #重新做raid

    def get_db_raid_info(self,tag,server_package):
        '''
            依据初始化信息，获取raid信息
        '''
        if tag == "data":
            sql = "select data_disk_num,data_disk_type,data_raid_info from pm_partition_rule where type = '%s'"
        elif tag == "other":
            sql = "select other_disk_num,other_disk_type,other_raid_info from pm_partition_rule where type = '%s'"
        elif tag == "sys":
            sql = "select sys_disk_num,sys_disk_type,sys_raid_info from pm_partition_rule where type = '%s'"


        result = super(Deal_Raid_info,self).select_advanced(sql,server_package)
 
        return result


    def  clean_raid(self,disk_type,raid_info):
        '''
            清理raid
            raid_info：排除对立的raid信息
        '''
        import itertools
        str_num = ""
        sql = "select virtual_group from disk_info where server_busi_ip in (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and virtual_group != 0 and disk_type = '%s' and raid_info != '%s'" 

        result= super(Deal_Raid_info,self).select_advanced(sql,self.host_ip,self.host_ip,disk_type,raid_info)

        if len(result) > 0: 
            
            it = ids = list(set(result))
            for num in it:
                level = "-L%s" % num
                cmd = "/opt/MegaRAID/MegaCli/MegaCli64 -CfgLdDel %s -force -a0" % level

                self.ssh_con.do_remote_by_passwd_exec(cmd)
                str_num = num + "," + str_num

            sql = "delete from disk_info where server_busi_ip in (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and virtual_group IN (%s)" 

            super(Deal_Raid_info,self).delete(sql,self.host_ip,self.host_ip,str_num[:-1])



    def check_raid_info(self,disk_num,disk_type,raid_info):
        '''
            检查raid

        '''
        result = ""
        sql = '''select * from (select disk_type,COUNT(virtual_group) AS disk_num from disk_info where server_busi_ip in (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and raid_info = '%s' and virtual_group != 0 GROUP BY virtual_group) as new_table where new_table.disk_num = %s and disk_type = '%s' '''

        result= super(Deal_Raid_info,self).select_advanced(sql,self.host_ip,self.host_ip,raid_info,disk_num,disk_type)

        return result

    def do_deal_raid(self,host_disk_num,host_raid_info):
        '''
            重做raid
        '''

        if host_raid_info == "NA":
            return
            
        if host_raid_info =="raid-0":
            r_info = "0"
        elif host_raid_info =="raid-1":
            r_info = "1"
        elif host_raid_info =="raid-5":
            r_info = "5"
        elif host_raid_info =="raid-10":
            r_info = "10"

        cmd = "/usr/local/sbin/sogou-raid -t create -r %s -n %s" % (r_info,host_disk_num)

        result,error = self.ssh_con.do_remote_by_passwd_exec(cmd)

        if result == "wrong":
            logger.write_log("host: %s,do raid failed! detail: %s" % (self.host_ip,error))
            return False
        else:
            return True


    def  set_disk_info(self,use_default_raid,server_package):
        '''
            处理分区信息，依据类型和数量
        '''
        host_busi_ip,server_status = "",""
        raid_name,disk_num = "",0
        result4data,result4other,result4sys = "","",""
        check4data,check4other   = "",""
        do_data_raid = False
        do_other_raid =False

        do_server_raid_dic = {}

        #按照默认格式
        if use_default_raid == 'yes':
            sql = "select host_busi_ip,server_status from server_info where host_data_ip = '%s' or host_busi_ip = '%s'"

            #查询服务器的业务网ip和服务器的可分配状态
            result = super(Deal_Raid_info,self).select_advanced(sql,self.host_ip,self.host_ip)
            
            if len(result) > 0:
                host_busi_ip = result[0][0]
                server_status = result[0][1]
            
            if server_status != 1 or len(result) == 0:

                result4data = self.get_db_raid_info("data",server_package)
                result4other = self.get_db_raid_info("other",server_package)
                
                #disk_num-->result4data[0][0]
                #disk_type-->result4data[0][1]
                #raid_info-->result4data[0][2]


                check4data = self.check_raid_info(result4data[0][0],result4data[0][1],result4data[0][2])


                check4other = self.check_raid_info(result4other[0][0],result4other[0][1],result4other[0][2])


                #由于只能同类型做raid,所以先做other后做data
                if len(check4other) != 1:
                    self.clean_raid(result4other[0][1],result4data[0][2])
                    if self.do_deal_raid(result4other[0][0],result4other[0][2]):
                       do_other_raid = True

                if len(check4data) != 1:
                    self.clean_raid(result4data[0][1],result4other[0][2])
                    if self.do_deal_raid(result4data[0][0],result4data[0][2]):
                       do_data_raid = True
                




                




