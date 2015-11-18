#!/usr/bin/python
# -*- coding: utf-8 -*-

import deal_ssh,common_lib
import re,sys,time
from mylib.base import Init_Base
import pprint

class Deal_Pm_Disk_Info(Init_Base):
    '''
        处理物理机硬盘信息,由于硬盘大小不固定
    '''
    def __init__(self,init_server_info,db_server_info):
        super(Deal_Pm_Disk_Info,self).__init__(init_server_info,db_server_info)

    def update_pm_info(self):
        '''
            更新pm_partition_rule表
        '''
        for server_info in self.init_server_info: 
            host_ip = server_info['client_server']['client_ip']
            package_type = server_info['client_server']['server_package']
            
            sql = "select data_disk_type,other_disk_type from pm_partition_rule where  type = '%s'"
            disk_type_result = super(Deal_Pm_Disk_Info, self).select_with_desc(sql,package_type)

            data_disk_type = disk_type_result[0]['data_disk_type']
            
            other_disk_type = disk_type_result[0]['other_disk_type']

            sql = "select disk_type,disk_size FROM `disk_info` where server_busi_ip = (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and disk_type = '%s' GROUP BY disk_size;"

            disk_data_result = super(Deal_Pm_Disk_Info, self).select_with_desc(sql,host_ip,host_ip,data_disk_type)

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



            
            
           