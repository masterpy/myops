#!/usr/bin/python
#-*- coding: UTF-8 -*-

import sys,os,time
import urllib2,socket
import argparse
from libs import my_lib,my_ping
from IPy import IP
import getpass
import multiprocessing
from progressbar import AnimatedMarker,FormatLabel,ReverseBar,ProgressBar


class Deploy_vlan_ip(object):
    def __init__(self):
        self.tool = my_lib.Public_tool()


    def input_by_name(self,tag):
        '''
            按照模块名方式输入,输入模块前请提前在bizmonitor平台配置好相关信息
        '''

        host_info = {}
        if tag == "deploy_by_name":
            show_header_info('deploy_by_name')

        elif tag == "switch_has_vlan":
            show_header_info('switch_has_vlan')

        elif tag == "show_vlan_info":
            show_header_info('show_vlan_info')

        while True:
            try:
                mode_name = raw_input("\n【相关Module Name可以在bizop平台(http://bizop.sogou-inc.com)进行查询】\n **请输入模块名称**  >>")
                #mode_name = "centre-dubhe"
                # my_lib.writelog("\n【相关Mode Name可以在bizop平台(http://bizop.sogou-inc.com)进行查询】\n **请输入模块名称** >>",'i',False)
                if mode_name.strip() == "":
                    continue
                elif mode_name.strip() == "exit":
                    my_lib.writelog("exit",'i')
                    main()
                elif mode_name.strip() == "quit":
                    if confirm_quit():
                        sys.exit(1)
            except KeyboardInterrupt:
                sys.exit(1)


            if self.tool.ipFormatChk(mode_name.strip()):
                my_lib.writelog("\033[1;31;40m**Error**\033[0m 输入的模块名非法!\n",'e')
                continue
            else:
                pass

            host_info = self.get_info_by_name(mode_name)

            if host_info:
                host_info['date_time'] = time.strftime("%Y-%m-%d %H:%M",time.localtime())
                host_info['user'] = getpass.getuser()
            else:
                continue

            if tag == 'deploy_by_name':
                result = self.set_info_by_name(host_info,'name')
                if result == 1:
                    my_lib.writelog("\033[1;32;40m**Success**\033[0m 配置vlan ip 成功.\n",'i')
                    content = my_lib.html_result(host_info,'vc')
                    if self.tool.send_email(content):
                        my_lib.writelog("\033[1;32;40m**Success**\033[0m 发送邮件 成功.\n",'i')
                        return
                    else:
                        my_lib.writelog("\033[1;31;40m**Error**\033[0m 发送邮件 失败! 请检查收件人是否配置正确.\n",'e')

                elif result == 2:
                    continue

                else:
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 配置vlan ip 失败!\n",'e')

            elif tag == 'switch_has_vlan' :
                result = self.switch_remote_vlanip(host_info)
                if  result == 1:
                    my_lib.writelog("\033[1;32;40m**Success**\033[0m 切换vlan ip 成功!\n",'i')
                    content = my_lib.html_result(host_info,'vs')
                    if self.tool.send_email(content):
                        my_lib.writelog("\033[1;32;40m**Success**\033[0m 发送邮件 成功!\n",'i')
                        return True
                    else:
                        my_lib.writelog("\033[1;31;40m**Error**\033[0m 发送邮件 失败! 请检查收件人是否配置正确.\n",'e')
                elif result == 2:
                    continue
                else:
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 切换vlan ip 失败!\n",'e')

            elif tag == 'switch_no_vlan':
                if self.switch_remote_ip(host_info):
                    my_lib.writelog("\033[1;32;40m**Success**\033[0m 切换server ip 成功!\n",'i')
                    content = my_lib.html_result(host_info,'ms')
                    if self.tool.send_email(content):
                        my_lib.writelog("\033[1;32;40m**Success**\033[0m 发送邮件 成功!\n",'i')
                        return True
                    else:
                        my_lib.writelog("\033[1;31;40m**Error**\033[0m 发送邮件 失败! 请检查收件人是否配置正确.\n",'e')
                else:
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 切换server ip 失败!\n",'e')

            elif tag == 'show_vlan_info':
                e1 = multiprocessing.Event()
                w1 = multiprocessing.Process(name='block',
                                 target=self.tool.timer_progress,
                                 args=(e1,))
                w1.start()
                self.show_vlanip_info(host_info,'switch')
                e1.set()
                w1.join()
                return True

            elif tag == 'check_vlan_net':
                e1 = multiprocessing.Event()
                w1 = multiprocessing.Process(name='block',
                                 target=self.tool.timer_progress,
                                 args=(e1,))
                w1.start()
                self.check_vlanip_network(host_info)
                e1.set()
                w1.join()
                return True

            else:
                my_lib.writelog("\033[1;31;40m**Error**\033[0m 非法参数.\n",'e')

    def check_vlanip_network(self,host_info):
        net_status = self.check_vlan_net(host_info['vipbusi'],host_info['vipdata'],host_info['mipbusi'],host_info['mipdata'])
        for key,value in net_status.items():
            if int(value) == 0:
                if key == host_info['vipbusi'] or key == host_info['vipdata']:
                  my_lib.writelog("\033[1;32;40m**Success**\033[0m vlan ip: %s  网络畅通.\n" % key,'i')
                  continue
                my_lib.writelog("\033[1;32;40m**Success**\033[0m machine ip: %s  网络畅通.\n" % key,'i')
            else:
                if key == host_info['vipbusi'] or key == host_info['vipdata']:
                    my_lib.writelog("\033[1;31;40m**Success**\033[0m vlan ip: %s  网络中断.\n" % key,'e')
                continue
                my_lib.writelog("\033[1;31;40m**Success**\033[0m machine ip: %s  网络中断.\n" % key,'e')

    def get_info_by_name(self,mode_name):
        '''
            依据模块名称获取hostinfo
        '''
        host_info = {}
        url = "http://10.13.195.150/system/server/getipinfo?busi_key=ip_switch&service=%(mode_name)s" % {'mode_name':str(mode_name)}
        host_info = self.tool.get_host_info(url)

        if host_info:
            return host_info
        else:
            my_lib.writelog("\033[1;31;40m**Error**\033[0m 无法获取主机信息.\n",'e')
            return False


    def set_info_by_name(self,host_info,tag):
        '''
            配置vlan ip
        '''
        # e = multiprocessing.Event()
        # w = multiprocessing.Process(name='block',
        #                          target=self.tool.timer_progress,
        #                          args=(e,))
        m_connect_ip = ""
        s_connect_ip = ""
        net_status = {}
        e1 = multiprocessing.Event()
        w1 = multiprocessing.Process(name='block',
                                 target=self.tool.timer_progress,
                                 args=(e1,))
        w1.start()
        m_connect_ip,s_connect_ip = self.get_alive_remote_ip(host_info['mipbusi'],host_info['mipdata'],host_info['sipbusi'],host_info['sipdata'] )

        if host_info['vipbusi'] is not None:

            net_status = self.check_vlan_net(host_info['vipbusi'],host_info['vipdata'])

            #从bizop获取得到vlan ip
            if net_status[host_info['vipbusi']] == 0 or net_status[host_info['vipdata']] == 0:
            #vlan ip存活,不能配置
                my_lib.writelog("\033[1;31;40m**Error**\033[0m vlan ip已在本地网络中其他机器配置,请联系系统管理员\n",'e')
                e1.set()
                w1.join()

                if confirm_info('quit'):
                    sys.exit(1)
                else:
                    return False
            else:

                if tag == 'name':
                    self.show_vlanip_info(host_info,'deploy')
                if tag == 'ip':
                    self.show_vlanip_info(host_info,'deploy_ip')

                e1.set()
                w1.join()
                if confirm_info('deploy'):
                    if len(m_connect_ip) > 0:

                        result = self.do_operation('deploy',host_info,m_connect_ip)

                        if result:
                            my_lib.writelog("\033[1;32;40m**Success**\033[0m 远程主机vlan ip部署成功!\n",'i')

                            return 1
                        else:
                            my_lib.writelog("\033[1;31;40m**Error**\033[0m 远程主机vlan ip部署 失败!\n",'i')
                    else:
                        my_lib.writelog("\033[1;31;40m**Error**\033[0m  远程主机:%s 网络不可达。失败!\n" % m_connect_ip,'e')
                else:
                    my_lib.writelog("\033[1;31;40m**Success**\033[0m 退出部署.\n",'i')
                    return 2
        else:
            my_lib.writelog("\033[1;31;40m**Error**\033[0m 该主机在bizop平台没有配置vlan ip.\n",'e')
        return False


    def input_by_ip(self):
        '''
            按照ip地址方式输入,必须验证ip合法性
        '''
        show_header_info('deploy_by_ip')
        while True:
            try:
                realip = raw_input("\n【退到主菜单输入 exit】请输入 \033[1;32;40m  Machine ip \033[0m;  >>")
            # my_lib.writelog("【退到主菜单输入 exit】请输入\033[1;32;40m Machine ip \033[0m;【**Not Vlan IP**】    >>",'i')

                if realip.strip() == "exit":
                    my_lib.writelog("exit",'i')
                    main()
                if len(realip.strip()) == 0:
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 输入的ip地址非法!\n",'e')
                    continue
                if realip.strip() == "quit":
                    if confirm_quit():
                        sys.exit(1)

            except KeyboardInterrupt:
                sys.exit(1)

            if self.tool.ipFormatChk(realip.strip()):
                real_ip = realip.strip()
            else:
                my_lib.writelog("\033[1;31;40m**Error**\033[0m 输入的ip地址非法!\n",'e')
                continue

            if my_ping.verbose_ping(real_ip):
                break
            else:
                my_lib.writelog("\033[1;31;40m**Error**\033[0m 网络不可达!\n",'e')
            continue

        while True:
            try:
                vlanip = raw_input("\n【退到主菜单输入 exit】请输入\033[1;32;40m VLAN IP \033[0m;  >>")

                if len(vlanip.strip()) == 0:
                    continue
                if vlanip.strip() == "exit":
                    my_lib.writelog("exit",'i')
                    main()
                if vlanip.strip() == "quit":
                    if confirm_quit():
                        sys.exit(1)

            except KeyboardInterrupt:
                sys.exit(1)


            if self.tool.ipFormatChk(vlanip.strip()):
                vlan_ip = vlanip.strip()
            else:
                my_lib.writelog("\033[1;31;40m**Error**\033[0m 输入的ip地址非法!\n",'e')
                continue


            url = "http://10.13.195.150/system/server/getserverinfo?busi_key=ip_switch&mip=%(real_ip)s&vip=%(vlan_ip)s" % {'real_ip':real_ip,'vlan_ip':vlan_ip}

            host_info = self.tool.get_hostinfo_by_ip(url,real_ip,vlan_ip)

            host_info['date_time'] = time.strftime("%Y-%m-%d %H:%M",time.localtime())
            host_info['user'] = getpass.getuser()

            if (host_info):
                result = self.set_info_by_name(host_info,'ip')
                if result == 1:
                    my_lib.writelog("\033[1;32;40m**Success**\033[0m  按照ip方式部署vlan ip 成功!\n",'i')
                    content = my_lib.html_result(host_info,'vc')
                    if self.tool.send_email(content):
                        my_lib.writelog("\033[1;32;40m**Success**\033[0m 发送邮件 成功!\n",'i')
                        return True
                    else:
                        my_lib.writelog("\033[1;31;40m**Error**\033[0m 发送邮件 失败! 请检查收件人是否配置正确.\n",'e')
                        break
                elif result == 2:
                    break
                else:
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m  按照ip方式部署vlan ip 失败!\n",'i')
                    break
            else:
                my_lib.writelog("\033[1;31;40m**Error**\033[0m 无法获取主机信息.\n",'e')
                break

        main()

    def check_vlanip_status(self,vlan_bussip,vlan_dataip,machineip):
        '''
            检查vlan ip是否在远程主机已配置
            vlan_bussip_confirm: 0:未配置  1:已配置一致 2:已配置不一致
            vlan_dataip_confirm: 0:未配置  1:已配置一致 2:已配置不一致
        '''
        vlan_ip_list = []

        vlan_bussip_confirm = False
        vlan_dataip_confirm = False

        command = 'cat /var/lib/vlan/vlan_stats | grep \"v_device_list\" | cut -d \":\" -f2'

        result_dev,error = self.tool.ssh_cmd(machineip,command)


        if len(error) == 0:
            for dev in result_dev.strip().split():
                command = 'ifconfig  %s | grep \"inet addr:\" | cut -d \":\" -f2 | awk \'{print $1}\'' % dev
                result,error = self.tool.ssh_cmd(machineip,command)
                vlan_ip_list.append(result.strip())

            if vlan_bussip in vlan_ip_list:
                vlan_bussip_confirm = 1

            else:
                if len(result) == 0:
                    vlan_bussip_confirm = 0
                else:
                    vlan_bussip_confirm = 2

            if vlan_dataip in vlan_ip_list:
                vlan_dataip_confirm = 1

            else:
                if len(result) == 0:
                    vlan_dataip_confirm = 0
                else:
                    vlan_dataip_confirm = 2


        return vlan_bussip_confirm,vlan_dataip_confirm


    def show_vlanip_info(self,host_info,tag):
        '''
            展示系统模块对应的vlan ip名称
            m_vlan_busi_status:主机 vlan ip 业务网配置状态
            m_vlan_data_status:主机 vlan ip 数据网配置状态
            s_vlan_busi_status:备机 vlan ip 业务网配置状态
            s_vlan_data_status:备机 vlan ip 数据网配置状态
        '''
        m_vlan_busi_status = '\033[1;32;40m 未配置 \033[0m'
        m_vlan_data_status = '\033[1;32;40m 未配置 \033[0m'
        s_vlan_busi_status = '\033[1;32;40m 未配置 \033[0m'
        s_vlan_data_status = '\033[1;32;40m 未配置 \033[0m'
        m_bussi_status     = '\033[1;31;40m 中断 \033[0m'
        m_data_status      = '\033[1;31;40m 中断 \033[0m'
        s_bussi_status     = '\033[1;31;40m 中断 \033[0m'
        s_data_status      = '\033[1;31;40m 中断 \033[0m'
        m_vlan_busi_ip       = '空'
        m_vlan_data_ip       = '空'
        s_vlan_busi_ip       = '空'
        s_vlan_data_ip       = '空'
        vlan_bussip_confirm  = False
        vlan_dataip_confirm  = False
        net_status = {}


        net_status = self.check_vlan_net(host_info['mipbusi'],host_info['mipdata'],host_info['sipbusi'],host_info['sipdata'])


        if host_info['isvirtual'] == "1":
            #虚拟机
            mc_name = "虚拟机"
        else:
            mc_name = "实体机"

        if net_status[host_info['mipbusi']] == 0:
            m_bussi_status = '\033[1;32;40m 正常 \033[0m'

        if net_status[host_info['mipdata']] == 0:
            m_data_status = '\033[1;32;40m 正常 \033[0m'

        if net_status[host_info['sipbusi']] == 0:
            s_bussi_status = '\033[1;32;40m 正常 \033[0m'

        if net_status[host_info['sipdata']] == 0:
            s_data_status =  '\033[1;32;40m 正常 \033[0m'

        if net_status[host_info['mipbusi']] == 1 and net_status[host_info['mipdata']] == 1:
            m_vlan_busi_status = '\033[1;31;40m 无法获取 \033[0m'
            m_vlan_data_status = '\033[1;31;40m 无法获取 \033[0m'
        if net_status[host_info['sipbusi']] == 1 and net_status[host_info['sipdata']] == 1:
            s_vlan_busi_status = '\033[1;31;40m 无法获取 \033[0m'
            s_vlan_data_status = '\033[1;31;40m 无法获取 \033[0m'


        m_connect_ip,s_connect_ip = self.get_alive_remote_ip(host_info['mipbusi'],host_info['mipdata'],host_info['sipbusi'],host_info['sipdata'] )

        #print "m_connect_ip,s_connect_ip",m_connect_ip,s_connect_ip

        if len(m_connect_ip) > 0 :
            #主机网络通畅,至少有一个网卡可以ping通
            if host_info['vipbusi' ] is not None or host_info['vipdata'] is not None:
                vlan_bussip_confirm,vlan_dataip_confirm = self.check_vlanip_status(host_info['vipbusi'],host_info['vipdata'],m_connect_ip)

            if vlan_bussip_confirm == 1:
                m_vlan_busi_status = '\033[1;32;40m 已配置 和bizop平台,数据一致 \033[0m'
                m_vlan_busi_ip = host_info['vipbusi']
            elif vlan_bussip_confirm == 2:
                m_vlan_busi_status = '\033[1;31;40m 已配置 和bizop平台,数据不一致 \033[0m'
                m_vlan_busi_ip = host_info['vipbusi']

            if vlan_dataip_confirm == 1:
                m_vlan_data_status = '\033[1;32;40m 已配置 和bizop平台,数据一致 \033[0m'
                m_vlan_data_ip = host_info['vipdata']
            elif vlan_dataip_confirm == 2:
                m_vlan_data_status = '\033[1;31;40m 已配置 和bizop平台,数据不一致 \033[0m'
                m_vlan_data_ip = host_info['vipbusi']

        if len(s_connect_ip) > 0:
            #备机网络通畅,至少有一个网卡可以ping通
            if host_info['vipbusi' ] is not None or host_info['vipdata'] is not None:
                vlan_bussip_confirm,vlan_dataip_confirm = self.check_vlanip_status(host_info['vipbusi'],host_info['vipdata'],s_connect_ip)

            if vlan_bussip_confirm:
                s_vlan_busi_status = '\033[1;32;40m 已配置 \033[0m'
                s_vlan_busi_ip = host_info['vipbusi']

            if vlan_dataip_confirm:
                s_vlan_data_status = '\033[1;32;40m 已配置 \033[0m'
                s_vlan_data_ip = host_info['vipdata']


        idc_name = self.tool.get_idc_name(host_info['mipbusi'])

        #print len(host_info['vipbusi'])
        if tag == 'deploy':
            print "*"*100
            my_lib.langage_data('output','1',mc_name,host_info['mipbusi'],m_bussi_status,host_info['mipdata'],m_data_status,idc_name,m_vlan_busi_status,m_vlan_data_status,m_vlan_busi_ip,m_vlan_data_ip)
            print "*"*100
            my_lib.langage_data('output','7',host_info['vipbusi'],host_info['vipdata'])
            print "*"*100
            my_lib.langage_data('output','3',host_info['service'],host_info['mipbusi'],host_info['mipdata'],host_info['sipbusi'],host_info['sipdata'],host_info['vipbusi'],host_info['vipdata'],'','','')
            print "*"*100
        elif tag == 'deploy_ip':
            my_lib.langage_data('output','1',mc_name,host_info['mipbusi'],m_bussi_status,host_info['mipdata'],m_data_status,idc_name,m_vlan_busi_status,m_vlan_data_status,m_vlan_busi_ip,m_vlan_data_ip)
            print "*"*100
            my_lib.langage_data('output','6',host_info['vipbusi'],host_info['vipdata'])
            print "*"*100

        elif tag == 'switch':
                print "*"*100
                my_lib.langage_data('output','1',mc_name,host_info['mipbusi'],m_bussi_status,host_info['mipdata'],m_data_status,idc_name,m_vlan_busi_status,m_vlan_data_status,m_vlan_busi_ip,m_vlan_data_ip)
                print "*"*100
                my_lib.langage_data('output','2',mc_name,host_info['sipbusi'],s_bussi_status,host_info['sipdata'],s_data_status,idc_name,s_vlan_busi_status,s_vlan_data_status,s_vlan_busi_ip,s_vlan_data_ip)
                print "*"*100
                my_lib.langage_data('output','3',host_info['service'],host_info['mipbusi'],host_info['mipdata'],host_info['sipbusi'],host_info['sipdata'],host_info['vipbusi'],host_info['vipdata'],' ',' ',' ')
                print "*"*100

    def get_alive_remote_ip(self,mipbusi,mipdata,sipbusi,sipdata):
        '''
            返回得到存活的，通畅的主备机ip地址
        '''
        m_connect_ip = ""
        s_connect_ip = ""
        net_status = {}


        if sipbusi is None or sipdata is None:
            net_status = self.check_vlan_net(mipbusi,mipdata)

        else:
            net_status = self.check_vlan_net(mipbusi,mipdata,sipbusi,sipdata)

            if net_status[sipbusi]  == 0 or net_status[sipdata] == 0:
                #备机网络通畅,至少有一个网卡可以ping通
                if net_status[sipbusi] < net_status[sipdata]:
                    s_connect_ip = sipbusi
                elif net_status[sipbusi] == net_status[sipdata]:
                    s_connect_ip = sipbusi
                else:
                    s_connect_ip = sipdata


        if net_status[mipbusi]  == 0 or net_status[mipdata] == 0:
            #主机网络通畅,至少有一个网卡可以ping通
            if net_status[mipbusi] < net_status[mipdata]:
                m_connect_ip = mipbusi
            elif net_status[mipbusi] == net_status[mipdata]:
                m_connect_ip = mipbusi
            else:
                m_connect_ip = mipdata

        return m_connect_ip,s_connect_ip


    def switch_remote_vlanip(self,host_info):
        '''
            切换(vlan ip和主机ip)主函数入口
        '''
        e1 = multiprocessing.Event()
        w1 = multiprocessing.Process(name='block',
                                 target=self.tool.timer_progress,
                                 args=(e1,))
        w1.start()
        m_connect_ip,s_connect_ip = self.get_alive_remote_ip(host_info['mipbusi'],host_info['mipdata'],host_info['sipbusi'],host_info['sipdata'] )

        self.show_vlanip_info(host_info,'switch')
        e1.set()
        w1.join()

        result = confirm_info('switch')
        if result:
            #如果备机网络通畅,主机宕机
            if len(m_connect_ip) == 0 and len(s_connect_ip) > 0:
                    result = self.do_operation('switch',host_info,s_connect_ip)
                    if result:
                        return 1
            #主机网络通畅,备机网络通畅
            elif len(m_connect_ip) > 0 and len(s_connect_ip) > 0:
                result = clean_info(m_connect_ip,"yes")
                if result:
                    result = self.do_operation('switch',host_info,s_connect_ip)
                    if result:
                        return 1
                else:
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 清理远程主机:%s vlan ip配置失败!\n" % m_connect_ip,'e')
            else:
                my_lib.writelog("\033[1;31;40m**Error**\033[0m 远程主机:%s 远程备机: %s 全部宕机!\n"(m_connect_ip,s_connect_ip),'e')
        else:
            my_lib.writelog("\033[1;31;40m**Success**\033[0m 退出部署.\n",'i')
            return 2

        return False


    def switch_remote_ip(self,host_info):
        '''
            切换server ip
        '''
        import commands
        e1 = multiprocessing.Event()
        w1 = multiprocessing.Process(name='block',
                                 target=self.tool.timer_progress,
                                 args=(e1,))
        e2 = multiprocessing.Event()
        w2 = multiprocessing.Process(name='block',
                                 target=self.tool.timer_progress,
                                 args=(e2,))

        mhostname = host_info['mhostname']
        shostname = host_info['shostname']
        master_busi_ip = host_info['mipbusi']
        master_data_ip = host_info['mipdata']
        slave_busi_ip = host_info['sipbusi']
        slave_data_ip = host_info['sipbusi']

        bash_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0],'bash_scripts')
        m_connect_ip,s_connect_ip = self.get_alive_remote_ip(host_info['mipbusi'],host_info['mipdata'],host_info['sipbusi'],host_info['sipdata'])

        if  host_info['vipbusi'] is None and host_info['vipdata'] is None:
            w1.start()
            self.show_vlanip_info(host_info,'switch')
            e1.set()
            w1.join()

            if confirm_info('switch'):
                #主机宕机，而备机畅通 传入s
                if len(m_connect_ip) == 0 and len(s_connect_ip) > 0:
                    w2.start()
                    cmd = "bash %(bash_dir)s/switch.sh %(opt)s %(mhostname)s %(shostname)s %(master_data_ip)s %(master_busi_ip)s %(slave_data_ip)s %(slave_busi_ip)s" % {'bash_dir':bash_dir,'opt':"s",'mhostname':mhostname,'shostname':shostname,'master_data_ip':master_data_ip,'master_busi_ip':master_busi_ip,'slave_data_ip':slave_data_ip,'slave_busi_ip':slave_busi_ip}

                    status,result = commands.getstatusoutput(cmd)
                    e2.set()
                    w2.join()

                    if not status:
                        return True
                    else :
                        return False

                elif len(m_connect_ip) > 0 and len(s_connect_ip) > 0:
                    #主机备机都畅通 传入ms
                    w2.start()
                    cmd = "bash %(bash_dir)s/switch.sh %(opt)s %(mhostname)s %(shostname)s %(master_data_ip)s %(master_busi_ip)s %(slave_data_ip)s %(slave_busi_ip)s" % {'bash_dir':bash_dir,'opt':"ms",'mhostname':mhostname,'shostname':shostname,'master_data_ip':master_data_ip,'master_busi_ip':master_busi_ip,'slave_data_ip':slave_data_ip,'slave_busi_ip':slave_busi_ip}
                    status,result = commands.getstatusoutput(cmd)
                    e2.set()
                    w2.join()

                    if not status:
                        return True
                    else :
                        return False
                else:
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 备机宕机，无法切换!\n",'e')
        else:
            my_lib.writelog("\033[1;31;40m**Error**\033[0m 此选项不支持vlan ip切换，请更换选项!\n",'e')
        return False

    def get_vlanip_info(self,mode_name):
        '''
            获取vlan ip信息
        '''
        url = "http://10.13.195.150/system/server/getipinfo?&busi_key=ip_switch&service=%(mode_name)s" % mode_name
        return self.tool.get_host_info(url)

    def check_vlan_net(self,*args):
        '''
            检查vlan ip 网络
            0 : 网络通
            1 : 网络不通
        '''

        net_status = {}
        if len(args) > 0:

            for ip in args:
                if ip is None:
                    net_status[ip] = 1

                elif my_ping.verbose_ping(ip):
                    net_status[ip] = 0
                else:
                    net_status[ip] = 1

            return net_status

    def do_deloy(self,host_info,remote_ip):
        '''
            执行新配置
        '''
        e = multiprocessing.Event()
        w = multiprocessing.Process(name='block',
                                 target=self.tool.timer_progress,
                                 args=(e,))

        if host_info['vipbusi' ] is not None and host_info['vipdata'] is not None:
            command = "/usr/bin/python /opt/opbin/tools/gerenate_route.py -b %(vipbusi)s -d %(vipdata)s -o add -m %(mc_type)s" % {'vipbusi':host_info['vipbusi'],'vipdata':host_info['vipdata'],'mc_type':host_info['isvirtual']}
            result,error_a = self.tool.ssh_cmd(remote_ip,command)
            if len(result) > 10:
                print result
                sys.exit(1)
            if len(error_a) == 0:
                w.start()
                command = "/bin/bash /opt/opbin/tools/scripts/vlan_start.sh csmode"
                result,error_b = self.tool.ssh_cmd(remote_ip,command)
                e.set()
                w.join()

                if result.strip() == "5":
                    return True
                elif result.strip() == "1":
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m vlan ip已经在网络中的其他服务器使用，请联系系统管理员.\n",'e')
                elif result.strip() == "2":
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 远程主机网卡启动失败.\n",'e')
                elif result.strip() == "3":
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 远程主机路由表不正确.\n",'e')
                elif result.strip() == "4":
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m 远程主机vlan ip网关不可达.\n",'e')
                else:
                    my_lib.writelog(error_b,'e')
            else:
                my_lib.writelog(error_a,'e')
        return False

    def do_switch(self,host_info,remote_ip):
        '''
            执行vlan ip切换的主函数
        '''
        #vlan ip在bizop平台已配置
        #print host_info
        if len(host_info['vipbusi']) > 0 and len(host_info['vipdata']) > 0:
            result = self.do_deloy(host_info,remote_ip)
            if result:
                return True
        my_lib.writelog("\033[1;31;40m**Error**\033[0m 无法获取vlan ip.\n",'e')
        return False


    def do_operation(self,action,host_info,remote_ip):
        '''
            执行操作选项的主函数
        '''

        if action == 'deploy':
            #新配置
            if self.do_deloy(host_info,remote_ip):
                return True
            else:
                return False

        elif action == 'switch':
            #vlan ip切换
            if host_info['vipbusi' ] is not None and host_info['vipdata'] is not None:
                temp = host_info['mipbusi']
                host_info['mipbusi'] =  host_info['sipbusi']
                host_info['sipbusi'] =  temp
                url = "http://10.13.195.150/system/server/updateservertype?busi_key=ip_switch&name=%s&vip=%s&sip=%s&mip=%s" % (host_info['service'],host_info['vipbusi'],host_info['sipbusi'],host_info['mipbusi'])
                if self.do_switch(host_info,remote_ip):
                    result = self.tool.update_bizmonitor(url)
                    if result:
                        my_lib.writelog("\033[1;32;40m**Success**\033[0m bizop平台信息更新成功.\n",'i')
                        return True
        return False




def show_header_info(tag):
    if tag == 'deploy_by_name':
        action_name = "*     DEPLOY VLAN IP     *"
        start_action = "Starting Deploy.%s" % ("."*85)
        note_info = "%sNote: 务必请先在bizop平台配置vlan ip，否则会导致vlan ip配置失败" % (" "*20)

    elif tag == 'deploy_by_ip':
        action_name = "*     DEPLOY VLAN IP     *"
        start_action = "Starting Deploy.%s" % ("."*85)
        note_info = "%sNote: 配置成功后，请更新bizop平台。" % (" "*30)

    elif tag == 'switch_has_vlan':
        action_name = "*     SWITCH VLAN IP     *"
        start_action = "Starting Switch Vlan ip.%s" % ("."*85)
        note_info = "%sNote: vlan ip切换成功后,请查收邮件。" % (" "*30)

    elif tag == 'switch_no_vlan':
        action_name = "*     SWITCH Server IP     *"
        start_action = "Starting Switch Server ip.%s" % ("."*85)
        note_info = "%sNote: server ip切换成功后,请查收邮件。" % (" "*30)

    elif tag == 'show_vlan_info':
        action_name = "*     SHOW HOST INFO     *"
        start_action = "Showing Server info.%s" % ("."*85)
        note_info = "%sNote: 查看主机配置信息以及bizop平台信息。" % (" "*20)

    elif tag == 'clean_by_ip':
        action_name = "*     CLEAN VLAN IP     *"
        start_action = "Starting CLEAN.%s" % ("."*85)
        note_info = "%sNote: 清理远程主机vlan ip配置前，请谨慎操作。" % (" "*20)


    print "\n"*1
    word = ""
    print(word.center(100,"*"))
    print
    print(action_name.center(90," "))
    print
    print(note_info.ljust(2))
    print
    word = ""
    print(word.center(100,"*"))
    print
    print start_action
    time.sleep(1)


def clean_info(remote_ip,tag="no"):
        '''
            清理配置
        '''
        tool = my_lib.Public_tool()
        e = multiprocessing.Event()
        w = multiprocessing.Process(name='block',
                                 target=tool.timer_progress,
                                 args=(e,))

        if tag == "yes":
            w.start()
            command = '/bin/bash /opt/opbin/tools/scripts/vlan_start.sh stop'
            result,error = tool.ssh_cmd(remote_ip,command)
            e.set()
            w.join()

            if len(error) == 0:
                command = '/usr/bin/python /opt/opbin/tools/gerenate_route.py -o del'
                result,error = tool.ssh_cmd(remote_ip,command)

                if len(error) == 0:
                    return True
                else:
                    my_lib.writelog("\033[1;31;40m**Error**\033[0m %s.\n" % error,'e')
                    return False
            else:
                my_lib.writelog("\033[1;31;40m**Error**\033[0m %s.\n" % error,'e')
                return False

            return True

def confirm_vlan_info(machineip):
    '''
        防止清理未配置vlan ip 服务的主机
    '''
    tool = my_lib.Public_tool()

    command = 'test -e \"/var/lib/vlan/vlan_stats\" && cat /var/lib/vlan/vlan_stats | grep \"v_device_list\" | cut -d \":\" -f2'
    result_dev,error = tool.ssh_cmd(machineip,command)

    if len(result_dev) == 0:
        my_lib.writelog("\033[1;31;40m**Error**\033[0m vlan ip 未配置!无法清理.\n",'e')
        return False

    for dev in result_dev.strip().split():
        command = 'ifconfig  %s | grep \"inet addr:\" | cut -d \":\" -f2 | awk \'{print $1}\'' % dev
        result,error = tool.ssh_cmd(machineip,command)
        if len(result) == 0:
            my_lib.writelog("\033[1;31;40m**Error**\033[0m vlan ip 未配置!无法清理.\n",'e')
            return False

        if result.strip() == machineip:
            my_lib.writelog("\033[1;31;40m**Error**\033[0m 输入ip地址非法,请输入机器的ip(eth0或者eth1)!\n",'e')
            return False

    return True


def clean_by_ip():
    '''
        清理远程主机的vlan ip配置
    '''
    tool = my_lib.Public_tool()
    show_header_info('clean_by_ip')
    while True:
        try:
            real_ip = raw_input("\n【退到主菜单输入 exit】请输入\033[1;32;40m remote Machine ip \033[0m;    >>")

            if real_ip.strip() == "exit":
                my_lib.writelog("exit",'i')
                main()

            if real_ip.strip() == "quit":
                if confirm_quit():
                    sys.exit(1)

        except KeyboardInterrupt:
            sys.exit(1)

        if tool.ipFormatChk(real_ip.strip()):
            realip = real_ip.strip()
        else:
            my_lib.writelog("\033[1;31;40m**Error**\033[0m 输入的ip地址非法!\n",'e')
            continue

        if my_ping.verbose_ping(realip):
            pass
        else:
            my_lib.writelog("\033[1;31;40m**Error**\033[0m 网络不可达!\n",'e')
            continue

        if confirm_vlan_info(realip):
            if confirm_info("clean"):
                if clean_info(realip,"yes"):
                    my_lib.writelog("\033[1;32;40m**Success**\033[0m  远程主机%s vlan ip配置清理成功!\n" % realip,'i')
            else:
                continue
        else:
            continue

def confirm_info(tag):
    '''
        退出部署
    '''
    if tag == 'quit':
        name = '\033[1;32;40m退出部署\033[0m'
    elif tag == 'deploy':
        name = '\033[1;32;40m进行绑定\033[0m'
    elif tag == 'switch':
        name = '\033[1;32;40m进行切换\033[0m'
    elif tag == 'clean':
        name = '\033[1;32;40m清理配置\033[0m'

    info = '【 请输入 y/n 】'
    while True:
        try:
            quit_info = raw_input("\n是否 %s%s  >>" % (name,info))
            # my_lib.writelog("\n是否 %s%s>>\n" % (name,info),i)
            print
            if quit_info.strip() == "y" or quit_info.strip() == "Y":
                #my_lib.writelog(quit_info,'i')
                return True
            if quit_info.strip() == "n" or quit_info.strip() == "N":
                #my_lib.writelog(quit_info,'i')
                return False
            if quit_info.strip() == "exit":
                my_lib.writelog("exit",'i')
                main()
            else:
                continue
        except KeyboardInterrupt:
            sys.exit(1)

def confirm_quit():
    info = '\033[1;32;40m【 请输入y/n 】 \033[0m'
    while True:
        try:
            name = raw_input("**是否退出** Quit? %s >> " % info)
            # my_lib.writelog("**是否退出** Quit? %s >> " % info,'i')
            if name.strip() == "y" or name.strip() == "Y":
                my_lib.writelog("\n\n\033[1;32;40m**Success**\033[0m Good Luck Boys.........\n",'i')
                return True
            elif name.strip() == "n" or name.strip() == "N":

                main()

            else:
                my_lib.writelog("%s" % info,'i')
                continue
        except KeyboardInterrupt:
            sys.exit(1)

def main():
    print "\n"*1
    word = ""
    print(word.center(100,"*"))
    #print ("DEPLOY VLAN IP - MAIN MENU")
    word = "*    DEPLOY OR SWITCH VLAN IP - MAIN MENU    *"
    print(word.center(90," "))
    print
    word = "%s1. deploy new vlan ip on remote server by ip" % (" "*20)
    print(word.ljust(2))
    word = "%s2. deploy new vlan ip on remote server by module_name" % (" "*20)
    print(word.ljust(2))
    word = "%s3. switch vlan ip on remote server by module_name" % (" "*20)
    print(word.ljust(2))
    word = "%s4. (when server has no vlan ip) switch ip on remote server by module_name" % (" "*20)
    print(word.ljust(2))
    word = "%s5. show vlan ip associated with module_name" % (" "*20)
    print(word.ljust(2))
    word = "%s6. clean vlan ip on remote server" % (" "*20)
    print(word.ljust(2))
    word = "%s7. check network for vlan ip" % (" "*20)
    print(word.ljust(2))
    word = "%s8. quit" % (" "*20)
    print(word.ljust(2))
    print
    word = ""
    print(word.center(100,"*"))
    print "\n"*2
    is_valid=0

    while not is_valid :
        try :
            choice = int ( raw_input('输入您的选择: [1-7] :'))
            is_valid = 1
        except ValueError, e :
            my_lib.writelog("\033[1;31;40m**Error**\033[0m 输入的选项不正确.\n",'e')
        except KeyboardInterrupt:
            sys.exit(1)


    deploy_cls = Deploy_vlan_ip()

    if choice == 1:
        deploy_cls.input_by_ip()

    elif choice == 2:
        deploy_cls.input_by_name('deploy_by_name')

    elif choice == 3:
        deploy_cls.input_by_name('switch_has_vlan')

    elif choice == 4:
        deploy_cls.input_by_name('switch_no_vlan')

    elif choice == 5:
        deploy_cls.input_by_name("show_vlan_info")

    elif choice == 6:
        clean_by_ip()

    elif choice == 7:
        deploy_cls.input_by_name("check_vlan_net")

    elif choice == 8:
        result = confirm_quit()
        if result:
            sys.exit(1)
    else:
        my_lib.writelog("\033[1;31;40m**Error**\033[0m 输入的选项不正确.\n",'e')


    result = confirm_quit()
    if result:
        sys.exit(1)


if __name__ == "__main__":
    main()
    
