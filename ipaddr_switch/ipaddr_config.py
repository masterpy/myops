#!/usr/bin/python
#-*- coding: UTF-8 -*-

import sys,os,time
import urllib2,socket
import commands
from libs import my_lib

import sys

#输入IP并且校验
def input_ip():
    '''
        输入IP并且校验
        返回：{'mc':mc,'vlanip_data':vlanip_data,'vlanip_busi':vlanip_busi,'reip':reip}
        其中：mc 为机器类型，reip 为机器的网卡ip地址
    '''
    tool = my_lib.Public_tool()
    status = 1
    status_a = 1
    my_lib.writelog(my_lib.langage_data('output','44'),'i')
    while status:
        real_ip = raw_input(my_lib.langage_data('input','1'))
        my_lib.writelog(my_lib.langage_data('input','1',real_ip),'i')
        if  real_ip == "q" or real_ip == "Q":
            sys.exit(1)

        vlan_ip = raw_input(my_lib.langage_data('input','2'))
        my_lib.writelog(my_lib.langage_data('input','2',vlan_ip),'i')

        real_ip = "10.134.65.37"
        vlan_ip= "10.134.224.102"

        ip_pool = tool.get_ip_value(real_ip,vlan_ip)
        if ip_pool:
            vlanip_busi = ip_pool['vlan_busi_ip']
            vlanip_data = ip_pool['vlan_data_ip']
            real_ip = ip_pool['real_data_ip']
        else:
            continue

        #检查vip 是否正在使用
        my_lib.writelog(my_lib.langage_data('output','6'),'i')
        if tool.ip_check(vlanip_data) or tool.ip_check(vlanip_busi):
            my_lib.writelog(my_lib.langage_data('output','3'),'w')
            continue

        #检查vlan ip,是否合法
        if not check_vlan_ip(real_ip,vlanip_data,vlanip_busi):
            continue
        else:
            mc = check_vlan_ip(real_ip,vlanip_data,vlanip_busi)

        ip_pool['mc'] = mc
        return ip_pool

#判断ip地址是否合法
def valid_ip(address):
    '''
        检查ip是否合法
    '''
    try:
        socket.inet_aton(address)
        return True
    except:
        return False

#检查vlan ip合理性
def check_vlan_ip(real_ip,vlan_ip1,vlan_ip2):
    data_vertify = {}
    tool = my_lib.Public_tool()

    api_url = '''http://10.13.195.150/system/server/verifyvlanip?busi_key=biztech&ip=%(real_ip)s&vip1=%(vlan_ip1)s&vip2=%(vlan_ip2)s''' % {'real_ip':real_ip,'vlan_ip1':vlan_ip1,'vlan_ip2':vlan_ip2}

    server_vertify_data = tool.get_url_data(api_url)
    if not server_vertify_data:
        sys.exit(1)

    message = server_vertify_data['message']

    if isinstance(message,dict):
        if message['result']:
            message_type = message['type']
            return message_type
        else:
            message_type = message['type']
            my_lib.writelog(my_lib.langage_data('output','5'),'e')
            return False
    else:
        print message
#        my_lib.writelog(my_lib.langage_data('output','15',message.decode('utf8')),'e')
        return False


def main():
    tool = my_lib.Public_tool()
    pool = input_ip()
    vlanip_data = pool['vlan_data_ip']
    vlanip_busi = pool['vlan_busi_ip']
    real_data_ip = pool['real_data_ip']
    real_busi_ip = pool['real_busi_ip']
    mc =  pool['mc']
    idc_name = pool['name']
    if mc == '0':
        pool['mc_name'] = "实体机"
    else:
        pool['mc_name'] = "虚拟机"


    my_lib.writelog(my_lib.langage_data('output','1',pool['mc_name'],real_busi_ip,real_data_ip,vlanip_busi,vlanip_data,idc_name,real_busi_ip,real_data_ip),'i')

    #开始绑定vlan ip
    ANS = raw_input(my_lib.langage_data('input','4'))
    my_lib.writelog(my_lib.langage_data('input','4',ANS),'i')

    while (ANS != "Y" or ANS != "y"):
        if  ANS == "Y" or ANS == "y":
            break
        if ANS == "N" or ANS == "n":
            my_lib.writelog(my_lib.langage_data('output','12'),'i')
            sys.exit(1)
        ANS = raw_input(my_lib.langage_data('input','4'))
        my_lib.writelog(my_lib.langage_data('input','4',ANS),'i')

    try:
            my_lib.writelog(my_lib.langage_data('output','9',vlanip_data),'i')
            cmd = "biztech-vlan -m %s -p %s -o add" % (mc,vlanip_data)
            tool.ssh_cmd(real_data_ip,cmd)
            os.system("sleep 3")

            my_lib.writelog(my_lib.langage_data('output','10',vlanip_busi),'i')
            cmd1 = "biztech-vlan -m %s -p %s -o add" % (mc,vlanip_busi)
            tool.ssh_cmd(real_data_ip,cmd1)
            os.system("sleep 3")

            my_lib.writelog(my_lib.langage_data('output','11'),'i')
            for  i in range(2):
                cmd3 = "bash /usr/local/sbin/biztech-vlanstart.sh"
                tool.ssh_cmd(real_data_ip,cmd3)
                os.system("sleep 3")
            os.system("sleep 3")

    except Exception,e:
            sys.exit(1)

    #检查是否配置好IP地址
    if tool.ip_check(vlanip_data) and tool.ip_check(vlanip_busi):
        my_lib.writelog(my_lib.langage_data('output','13'),'i')
    else:
       my_lib.writelog(my_lib.langage_data('output','14'),'i')

    my_lib.writelog(my_lib.langage_data('output','1',pool['mc_name'],real_busi_ip,real_data_ip,vlanip_busi,vlanip_data,idc_name),'i')

    ANS = raw_input(my_lib.langage_data('input','8'))
    while (ANS != "Y" or ANS != "y"):
        if  ANS == "Y" or ANS == "y":
            break
        if ANS == "N" or ANS == "n":
            my_lib.writelog(my_lib.langage_data('output','12'),'i')
            sys.exit(1)
        ANS = raw_input(my_lib.langage_data('input','8'))
        my_lib.writelog(my_lib.langage_data('input','8',ANS),'i')


    my_lib.writelog(my_lib.langage_data('output','47'),'i')
    pool['date_time'] = time.strftime("%Y-%m-%d %H:%M",time.localtime())
    content = my_lib.html_result(pool,'vc')
    tool.send_log_file(content)

if __name__ == "__main__":
    main()

