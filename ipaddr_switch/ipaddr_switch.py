#!/usr/bin/python
#-*- coding: UTF-8 -*-

import sys,time
from libs import my_lib


def validate_ip():
    '''
        校验vlan ip,防止忘记勾选模块，直接进行Ip切换
    '''
    tool = my_lib.Public_tool()
    while True:
        ip = raw_input(my_lib.langage_data('input','9'))
        my_lib.writelog(my_lib.langage_data('input','9',ip),'i')
        if ip == 'q' or ip == 'Q':
            sys.exit(1)
        url = "http://10.13.195.150/system/server/getvlanip?busi_key=biztech&ip=%s" % ip
        if tool.get_vlan_ip(url):
            my_lib.writelog(my_lib.langage_data('output','50'),'e')
            break
        else:
            my_lib.writelog(my_lib.langage_data('output','49'),'e')
            continue

def sendmessage(templist):
    '''发送邮件'''
    tool = my_lib.Public_tool()
    my_lib.writelog(my_lib.langage_data('output','47'),'i')
    content = my_lib.html_result(templist,'ms')
    tool.send_log_file(content)


def main():
    #存放 主机Ip，备机ip,vlan ip，邮件输出使用
    templist = {}
    host_id = {}
    host_info = {}
    tool = my_lib.Public_tool()
    validate_ip()
    my_lib.writelog(my_lib.langage_data('output','41'),'i')
    while True:
        model_sn = raw_input(my_lib.langage_data('input','5'))
        my_lib.writelog(my_lib.langage_data('input','5',model_sn),'i')
        if model_sn == "q" or model_sn == "Q":
            sys.exit(0)

        sn_api_url = "http://10.13.195.150/system/service/getlist?type=1&dept=1&name=%s&busi_key=biztech" % (model_sn)
        host_id = tool.get_host_id(sn_api_url)

        if not host_id:
            continue

        id_api_url = "http://10.13.195.150/system/service/getiplist?type=1&dept=1&id=%s&busi_key=biztech" % (host_id['id'])
        host_info = tool.get_host_info(id_api_url,host_id)

        if not host_info:
            continue

        stype = host_info['stype']
        sipbusi = host_info['sipbusi']
        sipdata = host_info['sipdata']
        shostname = host_info['shostname']
        mtype = host_info['mtype']
        mipbusi = host_info['mipbusi']
        mipdata = host_info['mipdata']
        mhostname = host_info['mhostname']
        mc = host_info['mc']
        vipbusi = host_info['vipbusi']
        vipdata = host_info['vipdata']

        my_lib.writelog(my_lib.langage_data('output','21'),'i')
        my_lib.writelog(my_lib.langage_data('output','1',mipdata,mipbusi),'i')
        my_lib.writelog(my_lib.langage_data('output','2',sipdata,sipbusi),'i')

        if host_id['is_vlanip'] == "1":
            my_lib.writelog(my_lib.langage_data('output','3',vipdata,vipbusi),'i')

        if mc == "0":
            mc_name = "实体机"
            my_lib.writelog(my_lib.langage_data('output','7'),'i')
        elif mc == "1":
            mc_name = "虚拟机"
            my_lib.writelog(my_lib.langage_data('output','8'),'i')

        my_lib.writelog(my_lib.langage_data('output','22',mhostname),'i')
        my_lib.writelog(my_lib.langage_data('output','23',shostname),'i')


        if vipbusi:
            if sipbusi:
                if mipbusi:
                    #切换完毕后，sipbusi 变成主ip对应mip, mipbusi变成备用ip对应sip
                    update_api_url = "http://10.13.195.150/system/server/updateservertype?busi_key=ip_switch&name=%s&vip=%s&sip=%s&mip=%s" % (model_sn,vipbusi,mipbusi,sipbusi)
                    ANS = raw_input(my_lib.langage_data('input','6'))
                    status = 1
                    my_lib.writelog(my_lib.langage_data('input','6',ANS),'i')
        else:
            ANS = raw_input(my_lib.langage_data('input','7'))
            status = 0
            my_lib.writelog(my_lib.langage_data('input','7',ANS),'i')

        templist = {'vlan_busi_ip':vipbusi,'vlan_data_ip':vipdata,'real_data_ip':mipdata,'real_busi_ip':mipbusi,'s_real_data_ip':sipdata,'s_real_busi_ip':sipbusi}
        templist['date_time'] = time.strftime("%Y-%m-%d %H:%M",time.localtime())


        while (ANS != "Y" or ANS != "y"):
            if  ANS == "Y" or ANS == "y":
                break
            if ANS == "N" or ANS == "n":
                my_lib.writelog(my_lib.langage_data('output','12'),'i')
                sys.exit(1)
            if status == 0:
                ANS = raw_input(my_lib.langage_data('input','7'))
                status = 0
                my_lib.writelog(my_lib.langage_data('input','7',ANS),'i')
            if status == 1:
                ANS = raw_input(my_lib.langage_data('input','6'))
                my_lib.writelog(my_lib.langage_data('input','6',ANS),'i')
            if  ANS == "Y" or ANS == "y":
                break


        if  ANS == "Y" or ANS == "y":
            if not vipdata:
                ret = tool.switch_ip(mhostname,shostname,mipdata,mipbusi,sipdata,sipbusi)
                if ret :
                    my_lib.writelog(my_lib.langage_data('output','24'),'i')
                else :
                    my_lib.writelog(my_lib.langage_data('output','25'),'i')
                    sys.exit(1)
            else :
                ret = tool.switch_service_ip(mc,mipdata,sipdata,vipdata,vipbusi)
                if ret :
                    my_lib.writelog(my_lib.langage_data('output','24'),'i')
                    if tool.update_bizmonitor(update_api_url):
                        my_lib.writelog(my_lib.langage_data('output','51'),'i')
                    else:
                        my_lib.writelog(my_lib.langage_data('output','52'),'i')
                        sys.exit(1)
                else :
                    my_lib.writelog(my_lib.langage_data('output','25'),'i')
                    sys.exit(1)


        #重新检查切换后信息
        host_info = tool.get_host_info(id_api_url,host_id)
        my_lib.writelog(my_lib.langage_data('output','1',host_info['mipdata'],host_info['mipbusi'],host_info['sipdata'],host_info['sipbusi'],host_info['vipdata'],host_info['vipbusi'],mc_name,host_info['mhostname'],host_info['shostname']),'i')

        ANS = raw_input(my_lib.langage_data('input','8'))
        while (ANS != "Y" or ANS != "y"):
            if  ANS == "Y" or ANS == "y":
                break
            if ANS == "N" or ANS == "n":
                my_lib.writelog(my_lib.langage_data('output','12'),'i')
                sys.exit(1)
            ANS = raw_input(my_lib.langage_data('input','8'))
            my_lib.writelog(my_lib.langage_data('input','8',ANS),'i')

        sendmessage(templist)
        break

main()
