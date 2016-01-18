#!/usr/bin/python
# -*- coding: utf-8 -*-

import common_lib
import re,sys,time
from mylib.base import Init_Base

class Deal_Pm_Disk_Info(Init_Base):
    '''
        处理物理机硬盘信息,由于硬盘大小不固定
    '''
    def __init__(self,db_server_info):
        super(Deal_Pm_Disk_Info,self).__init__(db_server_info)

    def get_pm_info_disk_num(self,host_ip,package_type):
        '''
            更新磁盘数量，目前只支持DX,CX
        ''' 
        support_type = ['C3','D1','D2','D3','c3','d1','d2','d3']
        if package_type in support_type:
            sql = "select count(*) as disk_num,disk_type from disk_info where server_busi_ip in ( select host_busi_ip from server_info WHERE ( host_busi_ip = '%s' or host_data_ip = '%s')) GROUP BY disk_type"

            disk_num_result = super(Deal_Pm_Disk_Info, self).select_with_desc(sql,host_ip,host_ip)
            if len(disk_num_result) == 1:
                disk_num = disk_num_result[0]['disk_num']
                data_disk_num  = int(disk_num) - 2
                sql = "update pm_partition_rule set disk_total = '%s',data_disk_num = '%s' where type = '%s'"
                super(Deal_Pm_Disk_Info,self).update_advanced(sql,disk_num,data_disk_num,package_type)
            else:
                print "host: %s.disk num error.please check it" % host_ip
                return False

        else:
            return

    def update_pm_info(self,host_ip,package_type):
        '''
            更新pm_partition_rule表
        '''
        sql = "select data_disk_type,other_disk_type from pm_partition_rule where  type = '%s'"
        disk_type_result = super(Deal_Pm_Disk_Info, self).select_with_desc(sql,package_type)

        data_disk_type = disk_type_result[0]['data_disk_type']
        if data_disk_type == 'SATA':
            data_disk_type = 'SSD'
        
        other_disk_type = disk_type_result[0]['other_disk_type']
        if other_disk_type == 'SATA':
            other_disk_type = 'SSD'

        sql = "select disk_type,disk_size FROM `disk_info` where server_busi_ip = (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and disk_type = '%s' GROUP BY disk_size;"

        disk_data_result = super(Deal_Pm_Disk_Info, self).select_with_desc(sql,host_ip,host_ip,data_disk_type)
       
        if len(disk_data_result) > 1:
            if  disk_data_result[0]['disk_size'][-2:-1] == disk_data_result[1]['disk_size'][-2:-1] == 'G':
                if int(round(float(disk_data_result[0]['disk_size'][:-2]))) > int(round(float(disk_data_result[1]['disk_size'][:-2]))):
                    data_disk_num = int(round(float(disk_data_result[0]['disk_size'][:-2])))
                else:
                    data_disk_num = int(round(float(disk_data_result[1]['disk_size'][:-2])))

                data_disk_cell = disk_data_result[0]['disk_size'][-2:-1]
                data_disk_size = str(data_disk_num) + data_disk_cell
            elif disk_data_result[0]['disk_size'][-2:-1] == 'T':
                data_disk_num = int(round(float(disk_data_result[0]['disk_size'][:-2])))*1024
                data_disk_cell = 'G'
                data_disk_size = str(data_disk_num) + data_disk_cell
            elif disk_data_result[1]['disk_size'][-2:-1] == 'T':
                data_disk_num = int(round(float(disk_data_result[1]['disk_size'][:-2])))*1024
                data_disk_cell = 'G'
                data_disk_size = str(data_disk_num) + data_disk_cell
        else:
            if disk_data_result[0]['disk_size'][-2:-1] == 'T':
                data_disk_num = int(round(float(disk_data_result[0]['disk_size'][:-2])))*1024
                data_disk_cell = 'G'
                data_disk_size = str(data_disk_num) + data_disk_cell
            else:
                data_disk_num = int(round(float(disk_data_result[0]['disk_size'][:-2])))
                data_disk_cell = disk_data_result[0]['disk_size'][-2:-1]
                data_disk_size = str(data_disk_num) + data_disk_cell

        sql = "update pm_partition_rule set data_one_disk_size = '%s' where type = '%s'"

        super(Deal_Pm_Disk_Info,self).update_advanced(sql,data_disk_size,package_type)



        if other_disk_type != 'NA':
            sql = "select disk_type,disk_size FROM `disk_info` where server_busi_ip = (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and disk_type = '%s' GROUP BY disk_size;"


            other_other_result = super(Deal_Pm_Disk_Info, self).select_with_desc(sql,host_ip,host_ip,other_disk_type)

            other_disk_num = int(round(float(other_other_result[0]['disk_size'][:-2])))
            other_disk_cell = other_other_result[0]['disk_size'][-2:-1]
            other_disk_size = str(other_disk_num) + other_disk_cell

            sql = "update pm_partition_rule set other_one_disk_size = '%s' where type = '%s'"

            super(Deal_Pm_Disk_Info,self).update_advanced(sql,other_disk_size,package_type)

        self.get_pm_info_disk_num(host_ip,package_type)
           