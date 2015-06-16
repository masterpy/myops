#!/usr/bin/python
# -*- coding: utf-8 -*-

import netifaces
from IPy import IP
import sys,os,shutil,random
import re
from vlan_lib import lib_net,sogouvlan
import pprint
import fileinput
import argparse

class Generate_ipaddr(object):
    '''
        生成ifcfg-ethX配置并配置相关ipv4地址
    '''
    def  __init__(self,device_type):
        self.device_type = int(device_type)


    def diff_data_bussi(self,ipdata):
        '''
            根据已配置的ip地址 找到数据网和业务网网卡名称
        '''
        temp_dic1 = {}
        temp_dic2 = {}
        temp_dic3 = {}
        temp_dic4 = {}

        if len(ipdata) > 0:
            for key,value in ipdata.items():
                for name,info in value.items():
                    if 'config_ipaddress' in name:
                        temp_dic1[key] = info
                    if 'alive_ipaddress'  in name:
                        temp_dic4[key] = info 

            for key1,value1 in temp_dic1.items():
                for  key4,value4 in temp_dic4.items():
                    if temp_dic1[key] == None and temp_dic4[key] != None:
                        print "adapter info is Erorr!"
                        sys.exit(1)

            for name in temp_dic1:
                temp_dic2[name[3:]] = name

            keys = temp_dic2.keys()
            keys.sort()
            temp_dic3 = map(temp_dic2.get,keys)

        if len(temp_dic3) > 2:
            if int(temp_dic1[temp_dic3[0]].split(".")[1]) < int(temp_dic1[temp_dic3[1]].split(".")[1]):
                ipdata[temp_dic3[0]]['bussi'] = False
                ipdata[temp_dic3[1]]['bussi'] = True
            else:
                print "adapter info is Erorr!"

            if temp_dic1[temp_dic3[2]] is not None and temp_dic1[temp_dic3[3]] is not None:
                if int(temp_dic1[temp_dic3[2]].split(".")[1]) < int(temp_dic1[temp_dic3[3]].split(".")[1]):
                    ipdata[temp_dic3[2]]['v_bussi'] = False
                    ipdata[temp_dic3[3]]['v_bussi'] = True           
                else:
                    print "adapter info is Erorr!"
            else:
                ipdata[temp_dic3[2]]['v_bussi'] = False
                ipdata[temp_dic3[3]]['v_bussi'] = True    

        elif len(temp_dic3) == 2:
            if int(temp_dic1[temp_dic3[0]].split(".")[1]) < int(temp_dic1[temp_dic3[1]].split(".")[1]):
                ipdata[temp_dic3[0]]['bussi'] = False
                ipdata[temp_dic3[1]]['bussi'] = True
        else:
            print "adapter num is Erorr!"

        return ipdata



    def get_ipaddr_data(self,vlan_tag_list):
        ''' 
            获取网卡配置以及对应的网卡名称
            type: 0 实体机
            type: 1 虚拟机
            vlan_tag_list: 实体机vlan_tag必须和实际匹配
        '''
        ipaddress,netmask,bootproto,onboot = "","","",""
        ifcfg_dic = {}
        ipdata = {}
        network_config_dir = "/etc/sysconfig/network-scripts"
        for dev_name in lib_net.get_network_interfaces():
            p = re.compile("usb*|lo*|br*|sit*")
            interface = eval(dev_name.get_data())
            matcher = p.match(interface['device'])
            if matcher:
                pass
            else:
                filename = "ifcfg-%s" % interface['device']
                device = interface['device']
                if os.path.exists(os.path.join(network_config_dir,filename)):
                    with open(os.path.join(network_config_dir,filename),'r')  as f:
                        for line in f.readlines():
                            if line.strip().startswith("IPADDR"):
                                ipaddress = line.strip().split("=")[1]
                            elif line.strip().startswith("NETMASK"):
                                netmask   = line.strip().split("=")[1]
                            elif line.strip().startswith("ONBOOT"):
                                onboot    =  line.strip().split("=")[1]
                            elif line.strip().startswith("BOOTPROTO"):
                                bootproto = line.strip().split("=")[1]

                    ifcfg_dic[device] = {
                    'device': device,
                    'alive_ipaddress':interface['IPv4'],
                    'netmask': netmask,
                    'onboot':onboot,
                    'bootproto':bootproto,
                    'index':interface['index'],
                    'vlan_tag':interface['index'],
                    'config_ipaddress':ipaddress,
                    'ifcfg_file':os.path.join(network_config_dir,filename),
                    }

                else:
                    ipaddress = None
                    netmask  = None
                    onboot   = None
                    ifcfg_dic[device] = {
                        'device': device,
                        'alive_ipaddress':interface['IPv4'],
                        'netmask': netmask,
                        'onboot':"no",
                        'bootproto':"static",
                        'index':interface['index'],
                        'vlan_tag':interface['index'],
                        'config_ipaddress':ipaddress,
                        'ifcfg_file':os.path.join(network_config_dir,filename),
                    }

        ipdata = self.diff_data_bussi(ifcfg_dic)

        if int(self.device_type) == 0:
            if len(ipdata) == 2:
                ipaddress = None
                netmask  = None
                onboot   = None
                for name,value in ipdata.items():
                    for opt,data in value.items():
                        #print data
                        if opt == 'bussi' and data:
                            oldfilename = "ifcfg-%s" % name
                            if vlan_tag_list[0] > vlan_tag_list[1]:
                                max_value = vlan_tag_list[0]
                            elif vlan_tag_list[0] < vlan_tag_list[1]:
                                max_value = vlan_tag_list[1]
                            

                            device = name + "." + str(max_value)
                            filename =  oldfilename + "." + str(max_value)

                            if device in interface['device']:
                                ipaddress = interface['IPv4']

                            ipdata[device] = {
                            'device': device,
                            'config_ipaddress':ipaddress,
                            'netmask': netmask,
                            'onboot':"no",
                            'bootproto':"static",
                            'index':max_value,
                            'vlan_tag':max_value,
                            'alive_ipaddress':ipaddress,
                            'ifcfg_file':os.path.join(network_config_dir,filename),
                            'v_bussi':True,
                            }

                        elif opt == 'bussi' and not data:
                            oldfilename = "ifcfg-%s" % name
                            if vlan_tag_list[0] < vlan_tag_list[1]:
                                min_value = vlan_tag_list[0]
                            elif vlan_tag_list[0] > vlan_tag_list[1]:
                                min_value = vlan_tag_list[1]
                            
                            

                            device = name + "." + str(min_value)
                            filename =  oldfilename + "." + str(min_value)

                            if device in interface['device']:
                                ipaddress = interface['IPv4']

                            ipdata[device] = {
                            'device': device,
                            'config_ipaddress':ipaddress,
                            'netmask': netmask,
                            'onboot':"no",
                            'bootproto':"static",
                            'index':min_value,
                            'vlan_tag':min_value,
                            'alive_ipaddress':ipaddress,
                            'ifcfg_file':os.path.join(network_config_dir,filename),
                            'v_bussi':False,
                            }


        if len(ipdata) == 4:
            return ipdata
        else:
            return  False

    def find_new_interface(self,vlan_tag_list):
        '''
            找到要配置的新网卡名称
            标记新网卡，业务网和数据网并返回
            vlan_tag_list: sogouvlan模块相关数据
            new_interface: 新网卡相关信息，值是字典
        '''
        list_index = []
        temp_list = []
        netface_value = {}
        new_interface = {}

        ifcfg_data = self.get_ipaddr_data(vlan_tag_list)

        return ifcfg_data


    def get_sogou_vlan_info(self,iplist):
        '''
            依据OP提供的信息生成对应的vlan 信息字典
        '''
        sogou_net_index = sogouvlan.IPMASK
        sogou_tag_index = sogouvlan.VLAN
        sogou_owner_index = sogouvlan.OWNER
        sogou_vlan_info = {}
        result_data = []
        for name,ip in iplist.items():
            for key,value in sogouvlan.vlaninfo.items():
                if ip in IP(value[sogou_net_index]):
                    sogou_vlan_info['netmask'] = IP(value[sogou_net_index]).netmask().strNormal()
                    sogou_vlan_info['gateway'] = IP(IP(value[sogou_net_index]).broadcast().int() - 1).strNormal()
                    sogou_vlan_info['net'] = value[sogou_net_index]
                    sogou_vlan_info['small_net'] = IP(value[sogou_net_index]).net().strNormal()
                    sogou_vlan_info['tag'] = value[sogou_tag_index]
                    sogou_vlan_info['ipaddress'] = ip
                    if name == 'vlanip_bussi':
                        sogou_vlan_info['v_bussi'] = True
                    else:
                        sogou_vlan_info['v_bussi'] = False

                    if sogou_vlan_info not in result_data:
                        result_data.append(sogou_vlan_info)
  
                    sogou_vlan_info = {}
                else:
                    continue

        return  result_data


    def set_ipaddr_data(self,vlan_ip_dic):
        '''
            生成ifcfg-ethX 配置文件
            vlan_ip_list 
        '''
        sogou_vlan_info = self.get_sogou_vlan_info(vlan_ip_dic)

        new_adapter_info = self.find_new_interface([sogou_vlan_info[0]['tag'],sogou_vlan_info[1]['tag']])
   
        num = str(random.random())[3:11]
        
        for name,adapter_info in new_adapter_info.items():
            for net_info in sogou_vlan_info:
                if 'v_bussi' in adapter_info and 'bussi' not in adapter_info:
                    if (adapter_info['v_bussi'] and net_info['v_bussi']) or (not adapter_info['v_bussi'] and not net_info['v_bussi']):
                        adapter_info['config_ipaddress'] = net_info['ipaddress']
                        adapter_info['netmask'] = net_info['netmask']

                        if int(self.device_type) == 1:
                            new_adapter_config = "DEVICE=%(device)s\nIPADDR=%(ipaddress)s\nNETMASK=%(netmask)s\nONBOOT=%(onboot)s\nBOOTPROTO=%(bootproto)s\n" % {'device':adapter_info['device'],'ipaddress':adapter_info['config_ipaddress'],'netmask':adapter_info['netmask'],'onboot':adapter_info['onboot'],'bootproto':adapter_info['bootproto']}

                        elif int(self.device_type) == 0:
                            new_adapter_config = "DEVICE=%(device)s\nIPADDR=%(ipaddress)s\nNETMASK=%(netmask)s\nONBOOT=%(onboot)s\nBOOTPROTO=%(bootproto)s\nISALIAS=%(isalias)s\nVLAN=%(vlan)s\n" % {'device':adapter_info['device'],'ipaddress':adapter_info['config_ipaddress'],'netmask':adapter_info['netmask'],'onboot':adapter_info['onboot'],'bootproto':adapter_info['bootproto'],'isalias':'yes','vlan':'yes'}

                        if os.path.exists(adapter_info['ifcfg_file']):
                            shutil.move(adapter_info['ifcfg_file'],'/tmp/%s' % (os.path.basename(adapter_info['ifcfg_file'] + "-" +num)))
                        with open(adapter_info['ifcfg_file'],'w') as f:
                            f.write(new_adapter_config)
                            f.close()

        return new_adapter_info


class Generate_route(Generate_ipaddr):
    '''
        生成main路由表以及rule规则表并修改/etc/iproute2/rt_tables
    '''
    def __init__(self,adapter_info,vlan_ip_dic):
        '''
            iplist: vlan_ip 列表
        '''
        self.adapter_info = adapter_info
        self.vlanip_list  = vlan_ip_dic


    def get_rule_data(self):
        '''
        获取到相关rule数据
        rule_info : key 为网卡名 value为rule_data
        rule_data ：存放rule以及自定义路由表相关数据

        '''
        rule_info = {}
        rule_data = {}
        rt_tables_num = []
        rt_tables = "/etc/iproute2/rt_tables"
        pattern = re.compile('^#')
        with open(rt_tables,'r') as f:
            for line in f.readlines():
                matcher = pattern.match(line)
                if matcher:
                    pass
                else:
                    num = line.split("\t")[0]
                    if len(num) > 4:
                        num = line.split(" ")[0]
                    rt_tables_num.append(num)

        sogou_vlan_info = Generate_ipaddr.get_sogou_vlan_info(self,vlan_ip_dic)

        for name,adapter_info in self.adapter_info.items():
            for net_info in sogou_vlan_info:
                if 'v_bussi' in adapter_info and 'bussi' not in adapter_info:
                    #生成vlan ip相关路由规则
                    if (adapter_info['v_bussi'] and net_info['v_bussi']) or (not adapter_info['v_bussi'] and not net_info['v_bussi']):
                        rule_data['vlan_net'] = net_info['net']
                        rule_info[adapter_info['device']] = rule_data                        
                        rule_data['gateway'] = net_info['gateway']
                        rule_data['rt_tables'] = rt_tables
                        rule_data['route_table'] = adapter_info['device'] + "_table"
                        rule_data['rule_file'] = os.path.dirname(adapter_info['ifcfg_file']) + "/rule-%s" % adapter_info['device']
                        rule_data['route_file'] = os.path.dirname(adapter_info['ifcfg_file']) + "/route-%s" % adapter_info['device']
                        rule_data['main_route_file'] = os.path.dirname(adapter_info['ifcfg_file']) + "/%s.route" % adapter_info['device']
                        while True:
                            table_num = random.randint(2, 253)
                            if table_num in rt_tables_num:
                                continue
                            else:
                                break
                        rt_tables_num.append(table_num)
                        rule_data['route_table_num'] = table_num
                        rule_data = {}

        return rule_info
        
    def get_main_route_data(self):
        '''
            将eth0.route eth1.route 拷一份生成为 eth2.route eth3.route 
        '''

        main_info = {}
        main_data = {}
        v_main_route_file = ""
        main_route_file = ""
        sogou_vlan_info = Generate_ipaddr.get_sogou_vlan_info(self,vlan_ip_dic)
        for name,adapter_info in self.adapter_info.items():
            if 'v_bussi' in adapter_info and adapter_info['v_bussi'] :
                v_main_route_bussi_file = os.path.dirname(adapter_info['ifcfg_file']) + "/%s.route" % adapter_info['device']

            elif 'bussi' in adapter_info and adapter_info['bussi']:
                main_route_bussi_file = os.path.dirname(adapter_info['ifcfg_file']) + "/%s.route" % adapter_info['device']
            
            elif 'v_bussi' in adapter_info and not adapter_info['v_bussi']:
                v_main_route_data_file = os.path.dirname(adapter_info['ifcfg_file']) + "/%s.route" % adapter_info['device']
            
            elif 'bussi' in adapter_info and not adapter_info['bussi']:
                main_route_data_file = os.path.dirname(adapter_info['ifcfg_file']) + "/%s.route" % adapter_info['device']

            else:
                continue

        shutil.copyfile(main_route_bussi_file,v_main_route_bussi_file)
        shutil.copyfile(main_route_data_file,v_main_route_data_file)

    def set_rule_data(self,rule_info):
        '''
            生成 route-ethX rule-ethX ethX.route相关文件以及数据
        '''
        priority_data =[]
        num = str(random.random())[3:11]
        priority = random.randint(1000,9000)

        #替换main 网关
        for name,info in rule_info.items():
            if os.path.exists(info['main_route_file']):
                pattern = re.compile("(GATEWAY[0-9]\=)(.*)",re.IGNORECASE)
                #print info['main_route_file']
                with open(info['main_route_file']) as f:
                    for line in f.readlines():
                        matcher = pattern.match(line)
                        if matcher:
                            gateway = matcher.group(2)
                    f.close()
                
                for line in fileinput.input(info['main_route_file'],inplace=True):
                    line = line.rstrip().replace(gateway,info['gateway'])
                    print line

            gateway = ""
            ifcfg_route_table_data = "%(vlan_net)s dev %(device)s scope link table %(route_table)s\ndefault via %(gateway)s dev %(device)s table %(route_table)s\n" %  {'vlan_net':info['vlan_net'],'device':name,'route_table':info['route_table'],'gateway':info['gateway']}
            ifcfg_rule_table_data  = "from %(vlan_net)s table %(route_table)s priority %(priority)s\n" %  {'vlan_net':info['vlan_net'],'route_table':info['route_table'],'priority':priority}
            ifcfg_rt_table_data    = "%(table_num)s\t%(table_name)s\n" % {'table_num':info['route_table_num'],'table_name':info['route_table']}

            #pprint.pprint(info)
            # if os.path.exists(info['route_file']):
            #     shutil.move(info['route_file'],'/tmp/%s' % (os.path.basename(info['route_file'] + "_" +num)))
            #     os.remove('/tmp/%s' % (os.path.basename(info['route_file'] + "_" +num)))

            # if os.path.exists(info['rule_file']):
            #     shutil.move(info['rule_file'],'/tmp/%s' % (os.path.basename(info['rule_file'] + "_" +num)))
            #     os.remove('/tmp/%s' % (os.path.basename(info['route_file'] + "_" +num)))
                    
            #替换rt_table中之前的配置
            route_table = "%s*" % info['route_table']
            pattern     = re.compile(route_table)
            rt_table_name = []

            cmd = "sed -i '/%s/d' /etc/iproute2/rt_tables" %  route_table
            if os.path.exists(info['rt_tables']):
                os.popen(cmd)


            with open(info['route_file'],'w') as f1,open(info['rule_file'],'w') as f2,open(info['rt_tables'],'a+') as f3:
                f1.write(ifcfg_route_table_data)
                f2.write(ifcfg_rule_table_data)
                f3.write(ifcfg_rt_table_data)
                f1.close()
                f2.close()

            priority_data.append(str(priority))
            priority = priority + 1
        return priority_data

def save_stats(adapter_info_value,rule_info,show_info,priority_data):
    '''
        保存信息到本地文件
        master_bussi_device_name: 主机业务网ip地址
        master_data_device_name:  主机数据网ip地址
        vbussi_device_name:       vlan ip所在业务网ip地址
        vdata_device_name:        vlan ip所在数据网ip地址
        v_device_list:            vlan ip所在网卡名称
        device_list:              物理ip(非vlan ip)所在网卡名称
        v_gateway:                vlan ip网关
    '''
    vlan_stats_dir  = "/var/lib/vlan/"
    vlan_stats_file = os.path.join(vlan_stats_dir,"vlan_stats")
    gateway_list,v_device_list,device_list,rt_table_list,vlan_net_list = [],[],[],[],[]
    
    vbussi_device_name,vbussi_ipaddr,master_bussi_device_name,m_bussi_ipaddr = "","","",""
    vdata_device_name,vdata_ipaddr,master_data_device_name,m_data_ipaddr     = "","","",""

    for name,adapter_info in adapter_info_value.items():
        if 'v_bussi' in adapter_info and adapter_info['v_bussi'] :
            vbussi_device_name =  adapter_info['device']
            vbussi_ipaddr      =  adapter_info['config_ipaddress']

        elif 'bussi' in adapter_info and adapter_info['bussi']:
            master_bussi_device_name =  adapter_info['device']
            m_bussi_ipaddr           =  adapter_info['config_ipaddress']

        elif 'v_bussi' in adapter_info and not adapter_info['v_bussi']:
            vdata_device_name = adapter_info['device']
            vdata_ipaddr      = adapter_info['config_ipaddress']
        elif 'bussi' in adapter_info and not adapter_info['bussi']:
            master_data_device_name = adapter_info['device']
            m_data_ipaddr           = adapter_info['config_ipaddress']
        else:
            continue

    v_device_list = "%s %s" % (vdata_device_name,vbussi_device_name)
    device_list   = "%s %s" % (master_data_device_name,master_bussi_device_name)
    
    #pprint.pprint(rule_info)
    for name,info in rule_info.items():
        gateway_list.append(info['gateway'])
        rt_table_list.append(info['route_table'])
        vlan_net_list.append(info['vlan_net'])

    stats_data = '''%(master_data_device_name)s: %(m_data_ipaddr)s\n%(master_bussi_device_name)s: %(m_bussi_ipaddr)s\n%(vdata_device_name)s: %(vdata_ipaddr)s\n%(vbussi_device_name)s: %(vbussi_ipaddr)s\nv_device_list: %(v_device_list)s\ndevice_list: %(device_list)s\nv_gateway: %(gateway_list)s\nrt_table_list: %(rt_table_list)s\nvlan_net_list: %(vlan_net_list)s\npriority:%(priority)s\n'''  % {'master_bussi_device_name':master_bussi_device_name,
    'm_bussi_ipaddr':m_bussi_ipaddr,
    'master_data_device_name':master_data_device_name,
    'm_data_ipaddr':m_data_ipaddr,
    'vbussi_device_name':vbussi_device_name,
    'vbussi_ipaddr':vbussi_ipaddr,
    'vdata_device_name':vdata_device_name,
    'vdata_ipaddr': vdata_ipaddr,
    'v_device_list':v_device_list,
    'device_list':device_list,
    'rt_table_list':" ".join(rt_table_list),
    'gateway_list':" ".join(gateway_list),
    'vlan_net_list':" ".join(vlan_net_list),
    'priority':" ".join(priority_data)}

    #pprint.pprint(stats_data)
    if not os.path.exists(vlan_stats_dir):
        os.makedirs(vlan_stats_dir)


    with open(vlan_stats_file,'w') as f:
        f.write(stats_data)
        f.close()

    if show_info:
        print stats_data

def del_adapter_info_data():
    '''
        移除网络配置
    '''
    import time
    pattern = re.compile("v_device_list.*")
    log_time = time.strftime("%Y_%m_%d",time.localtime())
    network_dir = "/etc/sysconfig/network-scripts"
    vlan_stats_dir  = "/var/lib/vlan/"
    vlan_stats_file = os.path.join(vlan_stats_dir,"vlan_stats")
    vlan_data = []

    if os.path.exists(vlan_stats_file):
        with open(vlan_stats_file,'r') as f:
            for line  in f.readlines():
                matcher = pattern.match(line)
                if matcher:
                    vlan_data = line.split(":")[1].strip().split(" ")

    else:
        print "/var/lib/vlan/vlan_stats is not exsit!"
        sys.exit(1)

    num = str(random.random())[3:11]
    for i in vlan_data:
        name = ".*%s.*" % i
        pattern1 = re.compile(name)

        for root,dirs,files in os.walk(network_dir):
            for filename in files:
                matcher1 = pattern1.findall(filename)
                if len(matcher1) > 0:
                    ifcfg_name =  os.path.join(network_dir,matcher1[0])
                    shutil.move(ifcfg_name,'/tmp/%s' % (matcher1[0] + "_" + log_time + "." + num))
                    os.remove('/tmp/%s' % (matcher1[0] + "_" + log_time + "." + num))

def check_init_file():
    if os.path.exists("vlan_lib/__init__.py"):
        os.remove("vlan_lib/__init__.py")
        with open("vlan_lib/__init__.py",'w') as f:
            f.close()

if __name__ == "__main__":
    check_init_file()
    adapter_info = {}
    priority_data = []
    parser = argparse.ArgumentParser(description='Config vlan ipaddress!')
    parser.add_argument('-b', action="store", dest="vlan_bussi_ipaddr",help="vlan ip业务网地址")
    parser.add_argument('-d', action="store", dest="vlan_data_ipaddr",help="vlan ip数据网地址")
    parser.add_argument('-o', action="store", dest="action",help="操作选项, 值为:del or add")
    parser.add_argument('-m', action='store', dest="mc_type",help="机器类型，值为:0 or 1,0:实体机 or 1:虚机")
    parser.add_argument('-v', action='store_true', dest="show_info",default=False,help="查看信息")
    results = parser.parse_args()

    if not results.action or results.action == "add":
        if not results.mc_type or not results.vlan_bussi_ipaddr or not results.vlan_data_ipaddr:
            parser.print_help()
            
    if results.action == "add":
    #添加网卡并保存状态
        import socket
        try:
            socket.inet_aton(results.vlan_bussi_ipaddr)
            socket.inet_aton(results.vlan_data_ipaddr)
        except socket.error,e:
            print e
            sys.exit(1)
        vlan_ip_dic = {'vlanip_bussi':results.vlan_bussi_ipaddr,'vlanip_data':results.vlan_data_ipaddr}
        ipaddr_cls = Generate_ipaddr(results.mc_type)
        adapter_info = ipaddr_cls.set_ipaddr_data(vlan_ip_dic)
        route_cls = Generate_route(adapter_info,vlan_ip_dic)
        rule_info = route_cls.get_rule_data()
        route_cls.get_main_route_data()
        priority_data = route_cls.set_rule_data(rule_info)
        save_stats(adapter_info,rule_info,results.show_info,priority_data)

    if results.action == "del":
    #删除vlan ip网卡配置
        del_adapter_info_data()





