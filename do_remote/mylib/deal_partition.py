#!/usr/bin/python
# -*- coding: utf-8 -*-

import deal_ssh,common_lib
import StringIO
import re,sys,time
from mylib.base import Init_Base

import pprint 


class Parted_Disk_init(Init_Base):
    '''
        处理分区信息类
    '''
    def __init__(self,init_server_info,db_server_info):
        super(Parted_Disk_init, self).__init__(init_server_info,db_server_info)

    def read_block_info(self):
        '''
            读取lvm 配置信息
        '''

        p1 = re.compile("^LV Name")
        p2 = re.compile("^VG Name")

        lvname,vgname = "",""
        swap = False

        lvm_info_command = "lvdisplay"
        pv_info_command  = "pvdisplay"

        lvm_info,blocks,partition_info,pv_info = {},{},[],{}
        begin = re.compile("(.*)Logical volume(.*)")
        end   = re.compile("Block device")
        new_block = False


        for server_info in self.init_server_info: 

            result,error = deal_ssh.remote_ssh_key_exec(server_info,lvm_info_command)
            
            if result == "wrong":
                print "host: %s . read lvm info failed." %  server_info['client_server']['client_ip']
                continue

            buf = StringIO.StringIO(result)
            
            for line in buf.readlines():
                line = line.strip()
                if new_block:
                    if end.match(line):
                        name = "%(vgname)s-%(lvname)s" % {'vgname':vgname,'lvname':lvname}
                        key = "dm-%s" % line.split()[-1].split(":")[-1]
                        blocks[key] = '/%s/%s/%s' % ('dev','mapper',name)
                        new_block = False

                    else:
                        if p1.match(line):
                            if len(line.split("/")) > 2:
                                lvname = line.split("/")[-1]
                            else:
                                lvname = line.split()[-1]
                            
                        elif p2.match(line):
                            vgname = line.split()[-1]
                else:
                    if begin.match(line):
                        new_block = True

            host_ip = server_info['client_server']['client_ip']
            lvm_info[host_ip] = blocks
            partition_info = []
            blocks = {}


            result,error = deal_ssh.remote_ssh_key_exec(server_info,pv_info_command)            
            if result == "wrong":
                print "host: %s . read pv info failed." %  server_info['client_server']['client_ip']
                continue
            buf = StringIO.StringIO(result)
            
            for line in buf.readlines():
                line = line.strip()
                if line.startswith("PV Name"):
                    pv_name = line.split()[2]
                    pv_info[host_ip] = pv_name

        return  lvm_info,pv_info


    def get_init_partition_info(self):
        '''
           查看block信息，返回数据盘信息,以及挂载信息 类似 df命令
        '''
        lvm_info,pv_info  = {},{}
        lvm_info,pv_info = self.read_block_info()
        
        idcname,host_busi_ip,host_data_ip = "","",""
        
        block_info = {} #存放分区信息
        result_info = {} #存放完整挂载信息
        server_partition_info = {} #存放完整服务器磁盘挂载信息

        block_info_command = "cat /proc/partitions"
        mounts_info_cmd    = "cat /proc/mounts"

        num  = re.compile("^[0-9](.*)")
        block_device_num = re.compile("[a-z]d[a-z][0-9]*")

        for server_info in self.init_server_info: 
            host_ip = server_info['client_server']['client_ip']
            
            if common_lib.get_idc_name(host_ip.strip()):
                idcname,host_busi_ip,host_data_ip = common_lib.get_idc_name(host_ip)
            else:
                print "get_idc_name failed."

        
            #分区信息
            result,error = deal_ssh.remote_ssh_key_exec(server_info,block_info_command)
            if result == "wrong":
                print "host: %s . read lvm info failed." %  server_info['client_server']['client_ip']
                continue

            templist = []
            buf = StringIO.StringIO(result)
            for line in buf.readlines():
                line = line.strip()
                for key,value in lvm_info.items():
                    if key.strip() == host_ip:
                        if num.match(line):
                            partition_mount_point    = "/dev/%s" % line.split()[-1] 
                            for alias_name,value_point in value.items():                        
                                if alias_name == line.split()[-1]:
                                    partition_mount_point = value_point

                            block_info[partition_mount_point] = {'partition_alias_name':line.split()[-1],'block_size':line.split()[-2],'block_num':line.split()[0]}


                if len(block_info) > 0:
                    templist.append(block_info)
                    block_info = {}
            

            #挂载信息
            result100,error = deal_ssh.remote_ssh_key_exec(server_info,mounts_info_cmd)
            if result100 == "wrong":
                print "host: %s . read lvm info failed." %  server_info['client_server']['client_ip']
                continue

            templist2,templist3,templist4 = [],[],[]
            partition_mount_point_list = []
            buf = StringIO.StringIO(result100)

            vgroot_rule = re.compile("(.*)vgroot-(.*)")
            lvm_rule = re.compile("(.*)lv(.*)")
            root_rule = re.compile("^\/dev\/root$")
            boot_rule = re.compile("(.*)(sda[0-9]|vda[0-9])$")

            for line in buf.readlines():
                line = line.strip()
                for blocks_info in templist:
                    for key,value in blocks_info.items():
                        #keys = key.replace("/","\/")
                        keys = key.split("/")[-1].split("-")
                        if len(keys) > 1 :
                            use_key = keys[1]
                            if use_key == "lvroot":
                                use_key = "root"
                        else:
                            use_key = keys[0]

                        p1 = re.compile("(.*)%s" % use_key)
                        
                        if p1.match(line):
                            if line not in templist2:
                                if line.split()[2] != "rootfs":
                                    partition_mount_point = line.split()[0]
                                    templist2.append(line)
                                    #整理/proc/mounts下的挂载点
                                    if not vgroot_rule.match(line.split()[0]):
                                        if lvm_rule.match(line.split()[0]):
                                            partition_mount_point = "/dev/mapper/vgroot-%s" % line.split()[0].split("/")[-1]
                          
                                    if root_rule.match(line.split()[0]):
                                        partition_mount_point = "/dev/mapper/vgroot-lvroot"

                                    result_info[partition_mount_point] = {'partition_name':line.split()[1],'partition_type':line.split()[2]}

                                    templist3.append(result_info)
                                    result_info = {}

            #区分挂载分区
            has_mount_partition = []
            #所有分区列表
            all_partition_list = []
            #存放挂载分区信息
            dictMerged1 = {}
            #存放非挂载分区信息
            dictMerged2 = {}

            swap = re.compile("(.*)swap(.*)")
            for blocks_info in templist:
                for key,value in blocks_info.items():
                    for partion_info in templist3:
                        if key in partion_info.keys():
                            has_mount_partition.append(key)
                            dictMerged1 = dict(partion_info[key].items() + blocks_info[key].items())
                            dictMerged1['partitions_point'] = key


                    if key not in has_mount_partition:
                        
                        dictMerged2 = blocks_info[key]
                        dictMerged2.setdefault('partition_name',"Null") 
                        dictMerged2.setdefault('partition_type',"Unknow")
                        dictMerged2.setdefault('partitions_point',"Unknow")
                        dictMerged2['partitions_point'] = key
                        if pv_info[host_ip] == key:
                            dictMerged2['partition_type'] = 'LVM'
                        if swap.match(key):
                            dictMerged2['partition_type'] = 'swap'
                            dictMerged2['partition_name'] = 'swap'

                    if len(dictMerged1) > 0:
                        all_partition_list.append(dictMerged1)
                    if len(dictMerged2) > 0:
                        all_partition_list.append(dictMerged2)
                    
                    #print dictMerged1
                    dictMerged1 = {}
                    dictMerged2 = {}

            server_partition_info[host_ip] = all_partition_list

        return server_partition_info


    def save_partition_info(self,server_partition_info):
        ''' 
            保存磁盘分区信息
        '''
        insert_id = 0
        idcname,host_busi_ip,host_data_ip = "","",""
        for host_ip,info in server_partition_info.items():
            if common_lib.get_idc_name(host_ip.strip()):
                idcname,host_busi_ip,host_data_ip = common_lib.get_idc_name(host_ip)
            else:
                print "get_idc_name failed."

            sql = "select `id` from server_info where host_data_ip = '%s' or host_busi_ip = '%s'"
            result  =  super(Parted_Disk_init, self).select_advanced(sql,host_data_ip,host_busi_ip)

            if len(result) > 0:
                server_id = result[0]
            else:
                server_id = -1 
             #先清理表
            sql  = "delete from partition_info where server_busi_ip = '%s'"
            super(Parted_Disk_init, self).delete(sql,host_busi_ip)

            for partitions in info:

                #更新表
                sql  = "insert into partition_info (server_id,server_busi_ip,partition_mount_point,block_num,partition_size,partition_name,partition_alias_name,partition_type) values (%s,'%s','%s','%s','%s','%s','%s','%s');"
                
                if int(partitions['block_size'])/1024/1024 > 0:   
                    size = str(int(partitions['block_size'])/1024/1024) + "G"
                else:
                    size = str(int(partitions['block_size'])/1024) + "M"

                insert_id = super(Parted_Disk_init, self).insert_advanced(sql,server_id,host_busi_ip,partitions['partitions_point'],partitions['block_num'],size,partitions['partition_name'],partitions['partition_alias_name'],partitions['partition_type'])

                if insert_id > 0:
                    pass


    def get_search_ted_info(self):
        '''
            处理search ted相关
        '''
        partition_dic = {}
        partition_dic['opt'] = {}
        partition_dic['ted'] = {}

        result,error = 0,0
        opt_mount = re.compile("(.*)opt")
        ted_mount = re.compile("(.*)ted")

        ext_rule = re.compile("ext[0-4]")
        xfs_rule = re.compile("xfs")

        for server_info in self.init_server_info: 
            host_ip = server_info['client_server']['client_ip']

            sql = "select partition_mount_point,partition_size,partition_type from partition_info where server_busi_ip = ( select host_busi_ip from server_info WHERE ( host_busi_ip = '%s' or host_data_ip = '%s')) and ( partition_mount_point like '%%lvted%%' or partition_mount_point like '%%lvopt%%')"

            for key in ['size','partition_type','partition_mount_point']:
                partition_dic['opt'].setdefault(key,'')
                partition_dic['ted'].setdefault(key,'')


            result = super(Parted_Disk_init, self).select_with_desc(sql,host_ip,host_ip)
            if len(result) > 0:
                for data in result:
                    if opt_mount.match(data['partition_mount_point']):
                        partition_dic['opt'] = {
                        'size':data['partition_size'],
                        'partition_type':data['partition_type'],
                        'partition_mount_point':data['partition_mount_point'],
                        }

                    elif ted_mount.match(data['partition_mount_point']):
                        partition_dic['ted'] = {
                        'size':data['partition_size'],
                        'partition_type':data['partition_type'],
                        'partition_mount_point':data['partition_mount_point'],
                        }

                    else:
                        continue

            if len(partition_dic['opt']['partition_mount_point']) > 0 and len(partition_dic['ted']['partition_mount_point']) > 0:

                #保证ted分区没有任何内容才能重新进行分区
                ted_subdir_exist_cmd = "test -e /search/ted&&ls /search/ted/ "
                result,error = deal_ssh.remote_ssh_key_exec(server_info,ted_subdir_exist_cmd)
                
                if len(result) > 0:
                    print "host: %s /search/ted is not NULL" % host_ip
                    return

                resize = "resize2fs"

                if len(partition_dic['opt']['partition_type']) > 0:
                    if  ext_rule.match(partition_dic['opt']['partition_type']):
                        resize = "resize2fs"
                    elif xfs_rule.match(partition_dic['opt']['partition_type']):
                        resize = "xfs_growfs"
                    else:
                        print "host: %s. FS is not correct!"
                        return 


                #size = int(partition_dic['ted']['partition_mount_point'][:-1]) - 10
                opt_size = '140G'
                
                remove_ted_cmd = "umount  %(ted_mount)s;lvremove -f %(ted)s;lvextend -L %(size)s %(opt)s;sed -i '/lvted/d' /etc/fstab;%(resize)s %(opt)s" % {'ted_mount':partition_dic['ted']['partition_mount_point'],'ted':partition_dic['ted']['partition_mount_point'],'size':opt_size,'resize':resize,'opt':partition_dic['opt']['partition_mount_point']}

                deal_ssh.remote_ssh_key_exec(server_info,remove_ted_cmd)



            
class Exec_partition_cls(Init_Base):
    '''
        执行划分分区 类
    '''
    def __init__(self,iplist,pmlist,db_server_info):
        super(Exec_partition_cls, self).__init__(iplist,db_server_info)
        self.iplist = iplist
        self.remote_user = "root"
        self.pmlist = pmlist


    def set_vm_partition_info(self):
        '''
            处理虚机分区信息
        '''
        new_partition_cmd,replace_partition_cmd = "",""
        data_partition = re.compile("(/data[0-9]*)")
        search_partition = re.compile("/search(.*)")


        exsit_data_partition = False
        exsit_partition = False


        new_partition_cmd = "mkfs.xfs /dev/vdb;mkdir /data;echo \"/dev/vdb  /data  xfs     defaults,noatime,nodiratime     0  0\" >>  /etc/fstab;mount -a"
        replace_partition_cmd = "umount /dev/vdb;sed -i '/\/dev\/vdb/d' /etc/fstab;echo \"/dev/vdb  /data  xfs     defaults,noatime,nodiratime     0  0\" >>  /etc/fstab;mkdir /data ;mount -a;df -h"

        for host_ip in self.iplist:
            sql =  "select partition_mount_point,partition_name from partition_info where server_busi_ip in (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and (partition_name like '%%search%%' or partition_name like '%%data%%')"
            
            result  =  super(Exec_partition_cls, self).select_with_desc(sql,host_ip,host_ip)
            partition_comfortable = 0

            for partitions_data in result:
                if data_partition.match(partitions_data['partition_name']):
                    exsit_data_partition = True
                elif search_partition.match(partitions_data['partition_name']):
                    exsit_search_partition = True
   
            if not exsit_data_partition:
                if not exsit_search_partition:
                    result = deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,new_partition_cmd)
                    if not result:
                        print "host: %s partition failed" % host_ip
                else:
                    result = deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,replace_partition_cmd)
                    if not result:
                        print "host: %s partition failed" % host_ip
            else:
                print "exsit_data_partition"


    def partition_new(self,host_ip,mount_dir,mount_type,mount_path):
        '''
            划分新分区信息
        '''

        if mount_type == 'xfs':
            format_str = "mkfs.xfs %s -f" % mount_path
        elif mount_type == 'ext3':
            format_str = "mkfs.ext3 %s -f " % mount_path
        elif mount_type == 'ext4':
            format_str = "mkfs.ext4 %s -f" % mount_path

        cmd = "%(format_str)s;mkdir -p %(new_mount_dir)s;echo \"%(path)s %(new_mount_dir)s  xfs   defaults,noatime,nodiratime  0 0\" >> /etc/fstab" % {'new_mount_dir':mount_dir,'path':mount_path,'format_str':format_str}
        deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,cmd)
        #return cmd
    
    def partition_rename(self,host_ip,new_mount_dir,new_mount_type,new_mount_path):
        '''
            重新挂载分区
        '''
        cmd  = "mkdir -p %(new_mount_dir)s;echo \"%(path)s %(new_mount_dir)s  %(new_mount_type)s   defaults,noatime,nodiratime  0 0\" >> /etc/fstab" % {'new_mount_dir':new_mount_dir,'path':new_mount_path,'new_mount_type':new_mount_type}
        deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,cmd) 
        #return cmd


    def clean_partion_old(self,host_ip,old_mount_dir,old_mount_path):
        '''
            清理老的分区
        '''
        if old_mount_dir == "Null":
            return 

        import string
        import random
        def id_generator(size=12, chars=string.ascii_lowercase + string.digits):
            return ''.join(random.choice(chars) for _ in range(size))

        str_sn = id_generator(12)
        

        new_mount_path = re.sub(r"/",r"\/",old_mount_path) 
        cmd = "fuser -ck %(mount_path)s;umount %(old_mount_dir)s;sed -i '/%(new_mount_path)s/d' /etc/fstab;/bin/cp /etc/fstab /tmp/fstab.%(str_sn)s" % {'mount_path':old_mount_path,'str_sn':str_sn,'new_mount_path':new_mount_path,'old_mount_dir':old_mount_dir}

        deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,cmd)
        #return cmd


    def get_new_mount_info(self,package_type):
        '''
            获取新的(自定义) 数据盘大小和其他盘大小
        '''
        sql = "select data_one_disk_size,data_raid_info,data_disk_num,data_mount_dir,data_mount_dir_file_type,other_one_disk_size,other_raid_info,other_disk_num,other_mount_dir,other_mount_dir_file_type from pm_partition_rule where type = '%s'" 
               
        result = super(Exec_partition_cls, self).select_with_desc(sql,package_type)

        #total_disk 硬盘大小
        total_disk_data = 0
        total_disk_other = 0

        mount_info_dic = {}

        for disk_info in result:
            if disk_info['data_raid_info'] == 'raid-5':
                total_disk_data = int(disk_info['data_one_disk_size'][:-1]) * (int(disk_info['data_disk_num']) - 1) 
                if disk_info['other_raid_info'] == 'raid-5':
                    total_disk_other = int(disk_info['other_one_disk_size'][:-1]) * (int(disk_info['other_disk_num']) - 1)
                elif disk_info['other_raid_info'] == 'raid-10' or disk_info['other_raid_info'] == 'raid-1':
                    total_disk_other = int(disk_info['other_one_disk_size'][:-1]) / 2
                else:
                    pass

            elif disk_info['data_raid_info'] == 'raid-10':
                total_disk_data = int(disk_info['data_one_disk_size'][:-1]) * int(disk_info['data_disk_num']) / 2

                if disk_info['other_raid_info'] == 'raid-5':
                    total_disk_other = int(disk_info['other_one_disk_size'][:-1]) * (int(disk_info['other_disk_num']) - 1)
                elif disk_info['other_raid_info'] == 'raid-10' or disk_info['other_raid_info'] == 'raid-1':
                    total_disk_other = (int(disk_info['other_one_disk_size'][:-1])*int(disk_info['other_disk_num']))/ 2
                else:
                    pass


            mount_info_dic['data'] = {'total_disk_data':total_disk_data,'data_mount_dir':disk_info['data_mount_dir'],'data_mount_dir_file_type':disk_info['data_mount_dir_file_type']}

            mount_info_dic['other'] = {'total_disk_other':total_disk_other,'other_mount_dir':disk_info['other_mount_dir'],'other_mount_dir_file_type':disk_info['other_mount_dir_file_type']}

        return mount_info_dic


    def compare_which_disk(self,standard_info,currently_mount_info_list):
        '''
            比较磁盘raid组大小,返回挂载目录等
        '''
        
        '''
        standard_info =
        {'data': {'data_mount_dir': u'/data',
          'data_mount_dir_file_type': u'xfs',
          'total_disk_data': 3900},
        'other': {'other_mount_dir': u'NA',
           'other_mount_dir_file_type': u'xfs',
           'total_disk_data': 0}}

        currently_mount_info_list =
           [{'/dev/sdd': {'relation': 'parent', 'size': '3625G'}},
            {'/dev/sdd1': {'relation': 'child', 'size': '3625G'}}]
        '''
       
        standard_data_size = 0
        standard_other_size = 0

        for cur_mount_info_key,cur_mount_info_value in currently_mount_info_list.items():
                currently_size = cur_mount_info_value['size']
                standard_data_size  = standard_info['data']['total_disk_data']
                standard_other_size = standard_info['other']['total_disk_other']
                
                if (int(currently_size[:-1]) > ( standard_data_size - 350)) and (int(currently_size[:-1]) < (  standard_data_size + 350)):
                    cur_mount_info_value['is_datadir'] = True
                    cur_mount_info_value['mount_file_type'] = standard_info['data']['data_mount_dir_file_type']
                    cur_mount_info_value['mount_dir'] = standard_info['data']['data_mount_dir']
                    


                if (int(currently_size[:-1]) > ( standard_other_size - 350)) and (int(currently_size[:-1]) < (  standard_other_size + 350)):

                    cur_mount_info_value['is_datadir'] = False
                    cur_mount_info_value['mount_file_type'] = standard_info['other']['other_mount_dir_file_type']
                    cur_mount_info_value['mount_dir'] = standard_info['other']['other_mount_dir']


        return currently_mount_info_list
             

    def set_machine_info(self,standard_info,currently_mount_info):
        '''
            返回挂载信息目录
        '''
        sort_mount_info_list = []
        mount_info_list = {}

        pattern = re.compile("(.*)(sd[b-z])$")
        
        for machine_item in currently_mount_info:
            if pattern.match(machine_item['partition_mount_point']):
                mount_info_list[machine_item['partition_mount_point']] = {'size':machine_item['partition_size']}
                mount_info_list[machine_item['partition_mount_point']]['relation'] = 'parent'
            else:
                mount_info_list[machine_item['partition_mount_point']] = {'size':machine_item['partition_size']}
                mount_info_list[machine_item['partition_mount_point']]['relation'] = 'child'
 
        return self.compare_which_disk(standard_info,mount_info_list)


    def  do_parted(self,host_ip,path,num):
        '''
            执行划分分区操作
        '''
        cmd = "parted %(path)s mklabel gpt -s;parted %(path)s mkpart primary 0 100%% -s;parted %(path)s name %(num)s data;" % {'path':path,'num':num}
        #print cmd
        deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,cmd)

    def finish_partition(self,host_ip):
        cmd = "mount -a"
        deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,cmd)


    def get_partition_data_by_ssh(self,host_ip):
        '''
            获取分区信息以及大小
        '''
        data_disk_pattern = re.compile("(.*)sd[b-z][0-9]*(.*)")
        #存放挂载点和挂载点大小
        temp_mount_dic = {}
        
        machine_partition_dic =  {}
        machine_partition_list = []

        get_partition_cmd = "cat /proc/partitions"

        ssh_result = deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,get_partition_cmd)

        buf = StringIO.StringIO(ssh_result)
        for line in buf.readlines():
            line = line.strip()
            if data_disk_pattern.match(line):
                temp_mount_dic['partition_mount_point'] = "/dev/%s" % line.split()[3]
                temp_mount_dic['partition_size'] = "%sG"  % str(int(line.split()[2])/1024/1024)            
                machine_partition_list.append(temp_mount_dic)
                machine_partition_dic[temp_mount_dic['partition_mount_point']] = temp_mount_dic['partition_size']
                temp_mount_dic = {}

        return machine_partition_list,machine_partition_dic


    def check_partition(self,host_ip,mount_data_list):
        '''
            检查挂载目录，挂载类型，重新挂载分区
        '''
        db_mount_info_dic = {}
        db_mount_info_list = []

        sql = "select partition_mount_point,partition_size,partition_name,partition_type from partition_info where server_busi_ip in (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s')  and partition_mount_point REGEXP '.*sd[b-z][0-9]*'"

        db_mount_result = super(Exec_partition_cls, self).select_with_desc(sql,host_ip,host_ip)

        #重做字典方便比对数据
        for db_mount_info  in db_mount_result:
            db_mount_info_dic[db_mount_info['partition_mount_point']] = {'old_mount_dir':db_mount_info['partition_name'],'old_mount_file_type':db_mount_info['partition_type'],'old_size':db_mount_info['partition_size']}

        #pprint.pprint(mount_data_list)
        #pprint.pprint(db_mount_info_dic)

        for cur_mount_info in mount_data_list:
            for mount_key,mount_value in cur_mount_info.items():
                #挂载点一致
                if mount_key in db_mount_info_dic:
                    #分区大小一致
                    if mount_value['size'] == db_mount_info_dic[mount_key]['old_size']:
                        #有子分区/dev/sdb1,sdc1等
                        if len(cur_mount_info) > 1:
                            #挂载子分区一致
                            if mount_value['relation'] == 'child':
                                #挂载目录一致
                                if mount_value['mount_dir'] == db_mount_info_dic[mount_key]['old_mount_dir']:
                                    #挂载类型一致
                                    if mount_value['mount_file_type'] == db_mount_info_dic[mount_key]['old_mount_file_type']:
                                        break
                                    else:
                                        #重新按照标准格式化分区
                                        self.clean_partion_old(host_ip,db_mount_info_dic[mount_key]['old_mount_dir'],mount_key)
                                        self.partition_new(host_ip,mount_value['mount_dir'],mount_value['mount_file_type'],mount_key)
                                else:
                                    self.clean_partion_old(host_ip,db_mount_info_dic[mount_key]['old_mount_dir'],mount_key)
                                    #挂载类型一致
                                    if mount_value['mount_file_type'] == db_mount_info_dic[mount_key]['old_mount_file_type']:
                                        #重命名目录
                                        self.partition_rename(host_ip,mount_value['mount_dir'],mount_value['mount_file_type'],mount_key)
                                    else:
                                        #重新按照标准格式化分区
                                        self.partition_new(host_ip,mount_value['mount_dir'],mount_value['mount_file_type'],mount_key)
                            else:
                                #卸载parent
                                self.clean_partion_old(host_ip,db_mount_info_dic[mount_key]['old_mount_dir'],mount_key)
                        ##没有子分区/dev/sdb1,sdc1等
                        else:
                            #新分区操作
                            self.clean_partion_old(host_ip,db_mount_info_dic[mount_key]['old_mount_dir'],mount_key)
                            #子分区命名为sdc1
                            self.do_parted(host_ip,mount_key,'1')
                            new_mount_path = mount_key + '1'
                            self.partition_new(host_ip,mount_value['mount_dir'],mount_value['mount_file_type'],new_mount_path)
                            break
                 
                    #分区大小不一致
                    else:
                        #新分区操作
                        self.clean_partion_old(host_ip,db_mount_info_dic[mount_key]['old_mount_dir'],mount_key)
                        if mount_value['relation'] == 'parent': 
                            #子分区命名为sdc1
                            self.do_parted(host_ip,mount_key,'1')
                            new_mount_path = mount_key + '1'
                            self.partition_new(host_ip,mount_value['mount_dir'],mount_value['mount_file_type'],new_mount_path)
                            break
                        else:
                            new_mount_key = mount_key[:-1]
                            #子分区命名为sdc1
                            self.do_parted(host_ip,new_mount_key,'1')
                            self.partition_new(host_ip,mount_value['mount_dir'],mount_value['mount_file_type'],mount_key)
                            break
                    #卸载用
                    
                #挂载点不一致
                else:
                    if len(cur_mount_info) == 2:
                        if mount_value['relation'] == 'parent': 
                            #新分区操作
                            self.do_parted(host_ip,mount_key,'1')
                            new_mount_path = mount_key + '1'
                            self.partition_new(host_ip,mount_value['mount_dir'],mount_value['mount_file_type'],new_mount_path)
                            break
                    else:
                        #新分区操作
                        self.do_parted(host_ip,mount_key,'1')
                        new_mount_path = mount_key + '1'
                        self.partition_new(host_ip,mount_value['mount_dir'],mount_value['mount_file_type'],new_mount_path)
                        break


        for cur_mount_info in mount_data_list:
            for mount_key2,mount_value2 in cur_mount_info.items():
                #挂载点一致
                if mount_key2 in db_mount_info_dic:
                    db_mount_info_dic.pop(mount_key2)

        for key,data in db_mount_info_dic.items():
            self.clean_partion_old(host_ip,data['old_mount_dir'],key)


    def set_pm_partition_info(self):
        '''
            处理实体机分区信息
        '''
        machine_partition_data = {}
        disk_num = re.compile('.*sdb[0-9]*')
        group_disk_info = re.compile("/dev/(sd[a-z])[0-9]*")

        for server_info in self.pmlist: 
            temp_size = 0
            host_ip = server_info['client_server']['client_ip']
            machine_partition_list,machine_partition_dic = self.get_partition_data_by_ssh(host_ip)
                  
            temp_disk_path_dic = {}
            temp_disk_path_info = []
            #分类，将sdb sdb1 sdb2等分到同一组内,主要是为了同分区做比对
            #machine_partition_list 为实时数据，不是数据库查询出的数据
            for disk_data_A in machine_partition_list:
                matchObjA  = group_disk_info.match(disk_data_A['partition_mount_point'])
                for disk_data_B in machine_partition_list:
                    matchObjB  = group_disk_info.match(disk_data_B['partition_mount_point'])
                    if matchObjA.group(1) == matchObjB.group(1):
                        key = matchObjA.group(1)
                        temp_disk_path_info.append(disk_data_B['partition_mount_point'])
                temp_disk_path_dic[key] = temp_disk_path_info
                temp_disk_path_info = []



            #依据套餐类型划分分区
            package_type = server_info['client_server']['server_package']

            #依据套餐类型存放数据盘和other盘的大小
            total_disk_size_dic = {}
            total_disk_size_dic = self.get_new_mount_info(package_type)


            #比较挂载目录，挂载类型,挂载点
            mount_info_list = []
            group_dic = {}
            mount_info_final = self.set_machine_info(total_disk_size_dic,machine_partition_list)
            
            #分组将/dev/sdb /dev/sdb1 分到一组，/dev/sdc,/dev/sdc1 分到一组
            for group_m_key,group_m_value in temp_disk_path_dic.items():
                for value in group_m_value:
                    group_dic[value] = mount_info_final[value]
                
                mount_info_list.append(group_dic)
                group_dic = {}
            

            #分区      
            self.check_partition(host_ip,mount_info_list)    
            self.finish_partition(host_ip)









