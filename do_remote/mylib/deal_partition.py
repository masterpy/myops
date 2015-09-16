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
                                    templist2.append(line)
                                    #整理/proc/mounts下的挂载点
                                    if not vgroot_rule.match(line.split()[0]):
                                        if lvm_rule.match(line.split()[0]):
                                            partition_mount_point = "/dev/mapper/vgroot-%s" % line.split()[0].split("/")[-1]
                                        else:
                                            partition_mount_point = line.split()[0]
                                    else:
                                        partition_mount_point = line.split()[0]

                                    if root_rule.match(line.split()[0]):
                                        partition_mount_point = "/dev/mapper/vgroot-lvroot"
                                    else:
                                        partition_mount_point = line.split()[0]

                           
                                    partition_mount_point_list.append(line.split()[0])
                                     
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
                    print dictMerged2
                    dictMerged1 = {}
                    dictMerged2 = {}

            server_partition_info[host_ip] = all_partition_list

        return server_partition_info


    def save_partition_info(self,server_partition_info):
        ''' 
            保存磁盘分区信息
        '''
        #print server_partition_info
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
                    print "update table partition_info success!"


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
                size = '140G'
                
                remove_ted_cmd = "umount  %(ted_mount)s;lvremove %(ted)s;lvextend -L %(size)s %(opt)s;sed -i '/lvted/d' /etc/fstab;/usr/bin/nohup %(resize)s %(opt)s &" % {'ted_mount':partition_dic['ted']['partition_mount_point'],'ted':partition_dic['ted']['partition_mount_point'],'size':size,'resize':resize,'opt':partition_dic['opt']['partition_mount_point']}

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
        search_partition = re.compile("/search")


        exsit_data_partition = False
        exsit_partition = False


        new_partition_cmd = "mkfs.xfs /dev/vdb;mkdir /data;echo \"/dev/vdb  /data  xfs     defaults,noatime,nodiratime     0  0\" >>  /etc/fstab;mount -a"
        replace_partition_cmd = "umount /search;sed -i s/search/data/g /etc/fstab;mkdir /data ;mount -a;df -h"

        for host_ip in self.iplist:
            sql =  "select partition_mount_point,partition_name from partition_info where server_busi_ip in (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and (partition_name like '%%search%%' or partition_name like '%%data%%')"
            
            result  =  super(Exec_partition_cls, self).select_with_desc(sql,host_ip,host_ip)
            partition_comfortable = 0

            for partitions_data in result:
                if data_partition.match(partitions_data['partition_name']):
                    exsit_data_partition = True
                    exsit_partition = True
                elif search_partition.match(partitions_data['partition_name']):
                    if exsit_data_partition:
                        exsit_partition = True
                        continue
   
            if not exsit_data_partition:
                if not exsit_partition:
                    result = deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,new_partition_cmd)
                    if not result:
                        print "host: %s partition failed" % host_ip
                else:
                    result = deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,replace_partition_cmd)
                    if not result:
                        print "host: %s partition failed" % host_ip
            else:
                print "exsit_data_partition"



    def do_partition(self,tag,host_ip,path,old_mount_dir,new_mount_dir):
        '''
            处理分区信息
        '''
        import string
        import random

        def id_generator(size=12, chars=string.ascii_lowercase + string.digits):
            return ''.join(random.choice(chars) for _ in range(size))

        str_sn = id_generator(12)

        print tag
        if tag == 'replace':
            cmd = "fuser -ck %(old_mount_dir)s;fuser -ck %(new_mount_dir)s;umount %(new_mount_dir)s;umount %(old_mount_dir)s;mkdir -p %(new_mount_dir)s;/bin/cp /etc/fstab /tmp/fstab.%(str_sn)s;sed -i '%(old_mount_dir)s/d' /etc/fstab;sed -i '%(new_mount_dir)s/d' /etc/fstab;echo \"%(path)s %(new_mount_dir)s  xfs   defaults,noatime,nodiratime  0 0\" >> /etc/fstab;mount -a" % {'old_mount_dir':old_mount_dir,'new_mount_dir':new_mount_dir,'str_sn':str_sn,'path':path}

        elif tag == 'new':
            cmd = "mkdir -p %(new_mount_dir)s;/bin/cp /etc/fstab /tmp/fstab.%(str_sn)s;echo \"%(path)s %(new_mount_dir)s  xfs   defaults,noatime,nodiratime  0 0\" >> /etc/fstab;mount -a" % {'new_mount_dir':new_mount_dir,'str_sn':str_sn,'path':path}
        else:
            return

        deal_ssh.remote_ssh_key_exec_simple_online(host_ip,self.remote_user,cmd)


    def set_pm_partition_info(self,pm_partition_data):
        '''
            执行划分分区主函数
        '''

        for host_ip in self.iplist:
            for path,new_mount_dir in pm_partition_data.items():
                if new_mount_dir == 'NA':
                    continue

                sql = "select partition_name from partition_info where server_busi_ip IN (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s') and partition_mount_point = '%s'"


                result  =  super(Exec_partition_cls, self).select_advanced(sql,host_ip,host_ip,path)

                old_mount_dir = result[0]
                print old_mount_dir
                if old_mount_dir == new_mount_dir:
                    pass
                elif old_mount_dir == "Null":
                    self.do_partition('new',host_ip,path,old_mount_dir,new_mount_dir)
                else:
                    self.do_partition('replace',host_ip,path,old_mount_dir,new_mount_dir)
                 



    def get_pm_partition_info(self):
        '''
            处理实体机分区信息
        '''

        disk_num = re.compile('.*sdb[0-9]*')

        disk_info = re.compile("/dev/(sd[a-z])[0-9]*")

        temp_size = 0
        temp_disk_path_info = []
        temp_disk_path_dic =  {}

        big_disk_info = []
        small_disk_info = []

        for server_info in self.pmlist: 
            host_ip = server_info['client_server']['client_ip']
            package_type = server_info['client_server']['server_package']
        
            #重要 查询分区表，得到sdb sdc等硬件路径，根据路径区分 哪些路径是正确的,哪些是冗余的
            sql = "select partition_mount_point,partition_size from partition_info where server_busi_ip in (select host_busi_ip from server_info where host_busi_ip = '%s' or host_data_ip = '%s')  and partition_mount_point REGEXP '.*sd[b-z][0-9]*'"

            result = super(Exec_partition_cls, self).select_with_desc(sql,host_ip,host_ip)

            if len(result) > 0:
                #分类，将sdb sdb1 sdb2等分到同一组内
                for disk_data_A in result:
                    matchObjA  = disk_info.match(disk_data_A['partition_mount_point'])
                    for disk_data_B in result:
                        matchObjB  = disk_info.match(disk_data_B['partition_mount_point'])
                        if matchObjA.group(1) == matchObjB.group(1):
                            key = matchObjA.group(1)
                            temp_disk_path_info.append(disk_data_B['partition_mount_point'])
                    temp_disk_path_dic[key] = temp_disk_path_info
                    temp_disk_path_info = []

                # #去重，如果同时存在sdb sdb1取sdb1 
                will_be_parted_path = []
                for key,value in temp_disk_path_dic.items():
                    if len(value) == 1:
                        will_be_parted_path.append(value[0])
                    else:
                        if value[0] > value[1]:
                            will_be_parted_path.append(value[0])
                        else:
                            will_be_parted_path.append(value[1])


                tempdic = {}
                for raw_disk_info in result:
                    for disk_path in will_be_parted_path:
                        if raw_disk_info['partition_mount_point'] == disk_path:
                            tempdic[disk_path] = raw_disk_info['partition_size']


              

                sql = "select data_one_disk_size,data_raid_info,data_disk_num,data_mount_dir,other_one_disk_size,other_raid_info,other_disk_num,other_mount_dir from pm_partition_rule where type = '%s'" 
               
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
                        total_disk_data = int(disk_info['other_one_disk_size'][:-1]) * int(disk_data_B['other_disk_num']) / 2

                        if disk_info['other_raid_info'] == 'raid-5':
                            total_disk_other = int(disk_info['other_one_disk_size'][:-1]) * (int(disk_info['other_disk_num']) - 1)
                        elif disk_info['other_raid_info'] == 'raid-10' or disk_info['other_raid_info'] == 'raid-1':
                            total_disk_other = int(disk_info['other_one_disk_size'][:-1]) / 2
                        else:
                            pass



                tempdic2 = {}

                for path,size in tempdic.items():
                    for disk_info in result:
                        if (int(size[:-1]) > ( total_disk_data - 200)) and (int(size[:-1]) < (  total_disk_data + 200)):
                            tempdic2[path] = disk_info['data_mount_dir']

                        elif (int(size[:-1]) > ( total_disk_other - 200)) and (int(size[:-1]) < (  total_disk_other + 200)):
                            tempdic2[path] = disk_info['other_mount_dir']
                        else:
                            pass

                return tempdic2







