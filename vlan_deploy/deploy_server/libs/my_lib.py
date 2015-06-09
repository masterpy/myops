#!/usr/bin/python
#-*- coding: UTF-8 -*-

import logging
import time
import os,sys,simplejson
import paramiko,commands
import urllib2
from ConfigParser import ConfigParser
import send_mail
from IPy import IP
import my_ping
import pprint

class Public_tool(object):
    def __init__(self):
        #初始化机房网段列表
        self.iplists = [
                        {'name':'石景山联通机房','data_ip':'10.134','busi_ip':'10.144'},
                        {'name':'土城联通机房_网段一','data_ip':'10.11','busi_ip':'10.13'},
                        {'name':'土城联通机房_网段二','data_ip':'10.137','busi_ip':'10.147'},
                        {'name':'永丰电信机房','data_ip':'10.139','busi_ip':'10.149'},
                        {'name':'大郊亭电信机房','data_ip':'10.12','busi_ip':'10.14'},
                        {'name':'新兆维电信机房','data_ip':'10.136','busi_ip':'10.146'},
                    ]
        self.host_id = {}.fromkeys(['id','is_vlanip'],None)
        self.host_info = {}.fromkeys(['isvirtual','sipbusi','sipdata','shostname','mipbusi','mipdata','mhostname','mc','vipbusi','vipdata'],None)


    #计时器
    def timer_progress(self,tag='no_end'):
        num = 60
        if  tag == 'end':
            return True
        while(num > 0):
            sys.stdout.flush()
            sys.stdout.write("\b"*1000)
            sys.stdout.write("Time Left: %d seconds Will Stop!" % num)
            sys.stdout.flush()
            num = num - 1
            time.sleep(1)

        writelog(langage_data('output','54'),'e')


    def get_hostinfo_by_ip(self,url,real_ip,vlan_ip):
        '''
        依据ip地址，生成hostinfo 格式类似通过modename获取到的
        '''
        server_vertify_data = self.get_url_data(url)
        if not server_vertify_data:
            return False

        if  server_vertify_data['success'] == 'true':
            for data in server_vertify_data['message']:
                if real_ip in data.values():
                    self.host_info['isvirtual'] = data.get('isxen')
                    self.host_info['service'] = ""
                    self.host_info['mipbusi'] = data.get('busi_ip')
                    self.host_info['mipdata'] = data.get('data_ip')
                    self.host_info['mc'] = data.get('isxen')
                elif vlan_ip in data.values():
                    self.host_info['vipbusi'] = data.get('busi_ip')
                    self.host_info['vipdata'] = data.get('data_ip')
            return self.host_info
        langage_data('output','55',server_vertify_data['message'])
        return False


    def get_host_info(self,url):
        '''
        依据模块获取主机配置信息
        '''
        num = 0
        server_vertify_data = self.get_url_data(url)
        if not server_vertify_data:
            return False
        #pprint.pprint(server_vertify_data['message'])

        if  server_vertify_data['success'] == 'true':
            if len(server_vertify_data['message']) <= 3:
                #只支持1主1备
                for value in server_vertify_data['message']:
                    self.host_info['isvirtual'] = value.get('isvirual')
                    self.host_info['service'] = "".join(value.get('service')) #列表

                    if value.get('type') == "0":
                        #0 表示备机
                        self.host_info['sipbusi'] = value.get('ipbusi')
                        self.host_info['sipdata'] = value.get('ipdata')
                        self.host_info['shostname'] = value.get('hostname')
                        self.host_info['servialid'] = value.get('servialid')
                        num = num + 1
                    elif value.get('type') == "1":
                        #1 表示主机
                        self.host_info['mipbusi'] = value.get('ipbusi')
                        self.host_info['mipdata'] = value.get('ipdata')
                        self.host_info['mhostname'] = value.get('hostname')
                        self.host_info['mc'] = value.get('isvirual')
                        self.host_info['servialid'] = value.get('servialid')
                        num = num + 1
                    elif value.get('type') == "2":
                        #2 表示vlan 
                        self.host_info['vipbusi'] = value.get('ipbusi')
                        self.host_info['vipdata'] = value.get('ipdata')
                        num = num + 1

                if num <= 3:
                    # pprint.pprint(self.host_info)
                    return  self.host_info
                else:
                    return False
            else:
                print  "not one to one"
                return False

        else:
            langage_data('output','55',server_vertify_data['message'])
            return False


    def get_idc_name(self,real_ip):
        '''
            依据ip地址，获取idc名称
            busi_ip: 主机业务网网卡ip(非vlan ip)
        '''

        if len(real_ip) == 0:
            return False

        real_ip_net = ".".join(IP(real_ip).strNormal().split('.')[:-2])
            
        for pool in self.iplists:
            if str(pool['busi_ip']) == str(real_ip_net):
                return pool['name']
            elif str(pool['data_ip']) == str(real_ip_net):
                return pool['name']


    def ssh_cmd(self,ip,command):
        port = 22
        username = 'root'
        key_file = "/root/.ssh/id_rsa"
        try:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname = ip, username =username, password='',pkey = private_key)
            stdin,stdout,sterr = client.exec_command(command,timeout = 10)
            result = stdout.read()
            error  = sterr.read()
            client.close()
            return result,error

        except Exception,e:
            #langage_data('output','16',e)
            print e
            #return 'None',e

    def ssh_check(self,ip):
        cmd = "ssh -o ConnectTimeout=3 %s 'hostname'"%(ip)
        status,ret = commands.getstatusoutput(cmd)
        if status == 0 :
            return True
        else :
            return False

    def get_url_data(self,url):
        '''
            返回接口值
        '''
        try:
            content_stream = urllib2.urlopen(url)
            content = content_stream.read()
            if content.strip().startswith("<b>" or "<B>"):
                writelog(langage_data('output','37'),'e')
                return False
            server_vertify_data = simplejson.loads(content.decode('gbk').encode('utf8'))
            return server_vertify_data

        except urllib2.HTTPError,e:
            langage_data('output','17',e)
            return False
        except urllib2.URLError,e:
            langage_data('output','18',e)
            return False
        except TypeError,e:
            langage_data('output','19')
            return False
        except simplejson.scanner.JSONDecodeError,e:
            langage_data('output','19')
            return False

    def update_bizmonitor(self,url):
        '''
        更新监控机
        '''
        langage_data('output','26')
        server_data = self.get_url_data(url)

        if "success" in server_data:
            if server_data['success'] == 'true':
                langage_data('output','27')
                return True
            else:
                langage_data('output','28',server_data["message"])
                return False
        else:
            langage_data('output','28',server_data["message"])
            return False

    def send_log_file(self,content):
        '''
        发送邮件，并清理缓存。
        '''
        maillist = {}
        conf_dir = os.path.join(os.path.split(__file__)[0])
        conf_file = "%s/%s" % (conf_dir,"mail.conf")
        logfile = "/tmp/opt.log"
        movelog()
        mailconf = Get_conf(conf_file)
        maillist = mailconf.get_value()
        mail = send_mail.Send_Email(maillist)
        if mail.sendText_Content(content):
            writelog(langage_data('output','43'),'i')
            os.remove(logfile)
        else:
            sys.exit(1)

    def check_network(self,ip):
        my_ping.verbose_ping(ip)


    def  check_valiate_vlanip(self,vlan_ip):
        '''
            利用vlan ip 反向连接服务器，作用如下:
            1. 验证ip和vlan ip是否匹配
            2. 检测vlan ip是否存活
        '''
        try:
            ip = IP(vlan_ip)
            command = ""
            server_result = self.ssh_cmd(ip,command)
        except ValueError,e:
            writelog(langage_data('output','2',vlan_ip),'i')



class Get_conf(ConfigParser):
    def __init__(self,config):
        ConfigParser.__init__(self)
        self.config  = config

    def get_value(self):
        '''
            读取配置文件
        '''
        args={}
        self.read(self.config)
        options = self.options('mail_conf')
        for values in options:
            args[values] = self.get('mail_conf',values)
        return args



def movelog():
    '''
    将缓存日志保存
    '''
    log_time = time.strftime("%Y_%m_%d",time.localtime())
    now_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0],'logs')
    if not os.path.exists(now_dir):
        os.makedirs(now_dir)
    log_file = "%(dir)s/%(local_time)s.log" % {'dir':now_dir,'local_time':log_time}

    src = file("/tmp/opt.log", "r+")
    des = file(log_file,"a+")
    des.writelines(src.read())
    src.close()
    des.close()


def writelog(string,tag):
    '''
    记录相关日志
    '''
    log_file = "/tmp/opt.log"
    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename=log_file,
                filemode='w')

    if tag == 'd':
            logging.debug(string)
    elif tag == 'i':
        logging.info(string)
    elif tag == 'w':
        logging.warning(string)
    elif tag == 'e':
        logging.error(string)
    else:
        print "文件IO错误."


def langage_data(src,tag,*args):
        if src == "input":
            input_data = {
                '1':'请输入将要在哪台机器上配置vlan ip\033[1;32;40mip地址，eth0,eth1均可 \033[0m 均可. 退出请输入Q >> %s' % ",".join(args),
                '2':'请输入要为此服务模块配置\033[1;32;40m的VLANIP \033[0m >> %s' % ",".join(args),
                '4':'\033[1;32;40m 请确认以上信息是否正确，是否进行IP绑定?确认，请输入(y/Y)，退出，请输入(n/N) \033[0m  >> %s ' % ",".join(args),
                '5':'请输入要切换的服务 \033[1;32;40m 模块名称 \033[0m,退出请输入Q >> %s' % ",".join(args),
                '6':'请确认是否进行IP切换[Y/N] >> %s' % ",".join(args),
                '7':'该模块没有 Vlan IP,请确认是否进行IP切换[Y/N] >> %s' % ",".join(args),
                '8':'请确认以上信息是否正确[Y/N] >> %s' % ",".join(args),
                '9':'为保证切换顺利，请输入需要切换的主机IP或者备机IP,退出请输入Q或q >> %s' % ",".join(args)
            }
            return input_data[tag]

        if src == "output":
            if len(args) == 0:
                out_data_none = {
                    '1':'\033[1;32;40m 正在校验这些ip地址请耐心等待！\033[0m........................................',
                    '3':'当前VLANIP已配置在其他机器中，换个IP吧',
                    '4':'权限未开通，请联系系统管理员!',
                    '5':'校验结果不匹配!请重新输入.',
                    '6':'正在检查这些ip地址是否已使用请耐心等待！....................................',
                    '7':'  机器类型:\033[1;32;40m 实体机 \033[0m',
                    '8':'  机器类型:\033[1;32;40m 虚拟机 \033[0m',

                    '11':'正在删除多余路由,\033[1;31;40m 请勿中断,删除中\033[0m................',
                    '12':'退出配置！.....................',
                    '13':'\033[1;32;40m IP配置完毕 \033[0m,请将VLAN录入bizmonitor',
                    '14':'\033[1;31;40m VLAN绑定失败，请联系系统管理员 \033[0m',
                    '19':'验证失败，该服务器没有相关接口权限。请联系开发管理员。',
                    '20':'此服务模块不具备切换条件，请重新输入!',
                    '21':'要切换的服务器信息如下 >> ',
                    '24':'\033[1;32;40m IP切换完毕,请等待20秒后尝试登录 \033[0m，如无法访问请联系系统管理员',
                    '25':'\033[1;31;40m IP切换失败，\033[0m 请联系系统管理员',
                    '26':'正在将新配置更新bizmonitor中.........',
                    '27':'bizmonitor 配置更新成功!',
                    '31':'正在进行IP切换....请耐心等待.',

                    '37':'没有相关权限.请联系管理员.',
                    '38':'输入参数不正确或者无法读取输入参数导致，请联系系统管理员.',
                    '39':'\033[1;31;40m 正在切换ip地址，请勿中断！\033[0m ....................................',
                    '40':'##############################\033[1;32;40m 切换 vlan ip \033[0m ##############################',
                    '41':'############################## \033[1;32;40m 切换 网卡ip \033[0m ##############################',
                    '43':'邮件发送完毕,ok!~~~~~~~',
                    '44':'##############################\033[1;32;40m 配置vlan ip  \033[0m ##############################',
                    '45':'\033[1;31;40m  没有该模块名称，请重新输入！！ \033[0m如果不知道该模块名称，请联系运维专员。',
                    '46':'\033[1;31;40m 非法ip地址。\033[0m',
                    '47':'\033[1;31;40m 正在发送邮件请耐心等待!............\033[0m',
                    '48':'切换完毕后的服务器信息如下:',
                    '49':'\033[1;31;40m  模块未勾选,主机对应的Vlan ip不存在!请先勾选响应的模块，并设置好vlan ip再进行切换。\033[0m',
                    '50':' \033[1;32;40m 验证通过，模块合法，ip合法。\033[0m',
                    '51':' \033[1;32;40m bizmonitor ip信息更新成功。\033[0m',
                    '52':'\033[1;31;40m bizmonitor ip信息更新失败。请手工更新。\033[0m',
                    '53':'\033[1;32;40m 邮件已成功发送,请查收邮件\033[0m',
                    '54':'访问系统超时，请检查网络是否正常。'
                }

                print out_data_none[tag]
                return out_data_none[tag]

            if len(args) == 1:
                out_data_one = {
                    '2':'%s \033[1;31;40m 是非法ip地址 \033[0m' % ",".join(args),
                    '9':'正在配置数据网IP: \033[1;32;40m %s \033[0m,请等待......' % ",".join(args),
                    '10':'正在配置业务网IP: \033[1;32;40m %s \033[0m,请等待......' % ",".join(args),
                    '15':'\033[1;31;40m %s \033[0m. 请重新输入.' % ",".join(args),
                    '16':'\033[1;31;40m Error! \033[0m ssh 认证失败，中控机无法登陆该机器，请配置ssh互信!错误如下: %s' % ",".join(args),
                    '17':'服务器端响应失败,返回状态码: \033[1;31;40m %s \033[0m' % ",".join(args),
                    '18':'无法到达服务器，网络不通，原因: %s' % ",".join(args),
                    '22':'  \033[1;31;40m当前主机\033[0m的hostname:\033[1;32;40m %s \033[0m' % ",".join(args),
                    '23':'  \033[1;31;40m备用主机\033[0m的hostname:\033[1;32;40m %s \033[0m'% ",".join(args),
                    '28':'bizmonitor 配置更新失败!原因如下: \n %s' % ",".join(args),
                    '29':'主机 \033[1;32;40m %s \033[0m 通过ssh 无法正常登陆，无法执行操作切换ip,请联系管理员!' % ",".join(args),
                    '30':'备机 \033[1;32;40m %s \033[0m 网络无法ping通。' % ",".join(args),
                    '31':'正在进行IP切换....请耐心等待.',
                    '32':'正在释放主机 vlan 服务IP: \033[1;32;40m %s. \033[0m' % ",".join(args),
                    '33':'主机IP: \033[1;32;40m %s \033[0m 无法删除路由，请重新确认，并联系系统管理员' % ",".join(args),
                    '34':'正在配置备机 Vlan 服务IP: \033[1;32;40m %s \033[0m' % ",".join(args),
                    '35':'业务网vlan ip \033[1;32;40m %s \033[0m 网络无法ping通，切换失败!' % ",".join(args),
                    '36':'数据网vlan ip \033[1;32;40m %s \033[0m 网络无法ping通，切换失败!' % ",".join(args),
                    '42':'无法正常发送邮件，请查看配置!邮件异常,错误为: %s' % ",".join(args),
                    '55':'\033[1;32;40m %s \033[0m,请联系系统管理员。'
                    }

                print out_data_one[tag]
                return out_data_one[tag]

            elif len(args) == 2:
                out_data_two = {
                '1':'  \033[1;31;40m主机\033[0m数据网网卡ip:\033[1;32;40m %s \033[0m[==] \033[1;31;40m主机\033[0m业务网网卡ip:\033[1;32;40m %s \033[0m' %  args,
                '2':'  \033[1;31;40m备机\033[0m数据网网卡ip:\033[1;32;40m %s \033[0m[==] \033[1;31;40m备机\033[0m业务网网卡ip:\033[1;32;40m %s \033[0m' %  args,
                '3':'  \033[1;31;40mVlan IP\033[0m 数据网ip:\033[1;32;40m %s \033[0m[==] \033[1;31;40mVlan IP\033[0m 业务网  ip:\033[1;32;40m %s \033[0m' %  args,
                '4':'主机 \033[1;32;40m %s \033[0m 切换失败,原因如下: \n %s ' % args,
                '5':'备机 \033[1;32;40m %s \033[0m 切换失败,原因如下: \n %s ' % args,
                '6' : '手工输入的:\n\nvlan ip信息如下:\n\n vlan ip的业务网地址: \033[1;32;40m %s\033[0m\n\n vlan ip的数据网地址: \033[1;32;40m %s\033[0m\n\n' % args,
                '7' : '主机即将绑定的:\n\nvlan ip信息如下:\n\n vlan ip的业务网地址: \033[1;32;40m %s\033[0m\n\n vlan ip的数据网地址: \033[1;32;40m %s\033[0m\n\n' % args,
                }
                print  out_data_two[tag]
                return out_data_two[tag]

            elif len(args) == 4:
                out_data_four = {
                '1' : 'Ip地址非法，请重新输入，其中 vipbusi是\033[1;32;40m %s \033[0m, sipbusi是\033[1;32;40m %s \033[0m,mipbusi是 \033[1;32;40m %s \033[0m .原因如下: \n %s' %  args,
            }
                print  out_data_four[tag]
                return out_data_four[tag]

            elif len(args) == 10:
                out_data_six = {
                    '1' : '''主机信息如下:\n\n 服务器类型: \033[1;32;40m %s\033[0m;\n\n 服务器的业务网ip地址: \033[1;32;40m %s\033[0m  网络:  %s \n\n 服务器的数据网ip地址: \033[1;32;40m %s\033[0m  网络:  %s \n\n 服务器所在机房: \033[1;32;40m%s\033[0m\n\n vlan ip所在业务网状态: %s \n\n vlan ip所在数据网状态: %s \n\n vlan ip 配置如下: %s / %s \n\n''' % args,
                    '2' : '''备机信息如下:\n\n 服务器类型: \033[1;32;40m %s\033[0m;\n\n 服务器的业务网ip地址: \033[1;32;40m %s\033[0m  网络:  %s \n\n 服务器的数据网ip地址: \033[1;32;40m %s\033[0m  网络:  %s \n\n 服务器所在机房: \033[1;32;40m%s\033[0m\n\n vlan ip所在业务网状态: %s \n\n vlan ip所在数据网状态: %s \n\n vlan ip 配置如下: %s / %s \n\n''' % args,
                    '3' : '''bizop平台获取到的信息如下:\n\n 模块名称:\033[1;32;40m %s\033[0m;\n\n 服务器(主机)的业务网ip地址: \033[1;32;40m %s\033[0m\n\n 服务器(主机)的数据网ip地址: \033[1;32;40m %s\033[0m\n\n 服务器(备机)的业务网ip地址: \033[1;32;40m %s\033[0m\n\n 服务器(备机)的数据网ip地址: \033[1;32;40m %s\033[0m\n\n vlan ip配置信息:\033[1;32;40m %s/%s \033[0m\n\n %s %s %s''' % args
 
            }
                print  out_data_six[tag]
                return out_data_six[tag]

            elif len(args) == 9:
                out_data_nine = {
                    '1' : '''
                    已经切换完毕的服务器信息如下:
                    主机数据网网卡ip: \033[1;32;40m%s\033[0m; [==] 主机业务网网卡ip: \033[1;32;40m%s\033[0m;
                    备机数据网网卡ip: \033[1;32;40m%s\033[0m; [==] 备机业务网网卡ip: \033[1;32;40m%s\033[0m;
                    Vlan IP 数据网ip: \033[1;32;40m%s\033[0m; [==] Vlan IP 业务网  ip: \033[1;32;40m%s\033[0m;
                    机器类型: \033[1;32;40m%s\033[0m;
                    当前主机的hostname: \033[1;32;40m%s\033[0m;
                    备用主机的hostname: \033[1;32;40m%s\033[0m;''' % args,
            }
                print  out_data_nine[tag]
                return out_data_nine[tag]


def html_result(data,tag):
    '''
    发送邮件内容
    '''
    if 'ms' == tag:
        out_data ='''<!doctype html>
                        <html lang="en">
                         <head>
                          <meta charset="UTF-8">
                         </head>
                         <STYLE>
                            m {color:DeepPink ;text-align:center}
                            sa {color:MediumBlue   ;text-align:center}
                            si {font-size:16px}
                         </STYLE>
                         <body>
                        <p><b>
                        <si>ip地址切换完毕!<br /><br />
                        ==========切换完成后，配置如下===========</si><br /><br />
                        <si>切换结束时间:</m>
                        <m>%(date_time)s</m><br />
                        <si>当前服务模块对外提供服务的主机网络配置如下:</si>&nbsp;&nbsp;<br />
                        <m>主机的数据网&nbsp;网卡ip地址:&nbsp;%(s_real_data_ip)s&nbsp;/&nbsp;主机的业务网&nbsp;网卡ip地址:&nbsp;%(s_real_busi_ip)s</m><br />
                        <si>当前服务器备机网络配置如下:</si><br />
                        <sa>备机的数据网&nbsp;网卡ip地址:&nbsp;%(real_data_ip)s&nbsp;/&nbsp;备机的业务网&nbsp;网卡ip地址:&nbsp;%(real_busi_ip)s</sa><br /><br />
                        <si>==========切换完成前，配置如下===========</si><br /><br />
                        <si>原服务模块对外提供服务的主机网络配置如下:</si>&nbsp;&nbsp;<br />
                        <m>原主机数据网&nbsp;网卡ip地址:&nbsp;%(real_data_ip)s&nbsp;/&nbsp;原主机业务网&nbsp;网卡ip地址:&nbsp;%(real_busi_ip)s</m><br />
                        <si>原服务模块备机网络配置如下:</si><br />
                        <sa>原备机数据网&nbsp;网卡ip地址:&nbsp;%(s_real_data_ip)s&nbsp;/&nbsp;原备机业务网&nbsp;网卡ip地址:&nbsp;%(s_real_busi_ip)s</sa><br /><br />
                        </body>
                        </html>''' % {'date_time':data['date_time'],'real_data_ip':data['real_data_ip'],'real_busi_ip':data['real_busi_ip'],'s_real_data_ip':data['s_real_data_ip'],'s_real_busi_ip':data['s_real_busi_ip']}
    elif 'vs' == tag:
        out_data ='''<!doctype html>
                        <html lang="en">
                         <head>
                          <meta charset="UTF-8">
                         </head>
                         <STYLE>
                            m {color:DeepPink ;text-align:center}
                            vs {color:Red;text-align:center}
                            sa {color:MediumBlue   ;text-align:center}
                            si {font-size:18px}
                            sim {font-size:14px}
                         </STYLE>
                         <body>
                        <p><b>
                        <si>vlan ip地址切换完毕!<br /><br />
                        ==========切换完成后，网络配置如下===========</si><br /><br />
                        <si>切换结束时间:</m>
                        <m>%(date_time)s</m><br /><br />
                        <sim>--------------------------------------------------------------------------------------</sim><br />
                        <vs>当前vlan ip 网卡配置如下:</vs><br />
                        <sim>对外提供服务的业务网vlan ip:</sim>&nbsp;&nbsp;
                        <m>%(vlan_busi_ip)s</m><br />
                        <sim>对外提供服务的数据网vlan ip:</sim>&nbsp;&nbsp;
                        <m>%(vlan_data_ip)s</m><br />
                        <sim>--------------------------------------------------------------------------------------</sim><br />
                        <vs>当前vlan ip绑定的主机网卡配置如下:</vs><br />
                        <sim>当前主机数据网&nbsp;网卡IP地址:&nbsp;<m>%(s_real_data_ip)s</m></sim><br />
                        <sim>当前主机业务网&nbsp;网卡IP地址:&nbsp;<m>%(s_real_busi_ip)s</m></sim><br />
                        <sim>--------------------------------------------------------------------------------------</sim><br />
                        <vs>当前未绑定vlan ip的备机网卡配置如下:</vs><br />
                        <sim>当前未绑定备机数据网&nbsp;网卡IP地址:&nbsp;<m>%(real_data_ip)s</m></sim><br />
                        <sim>当前未绑定备机业务网&nbsp;网卡IP地址:&nbsp;<m>%(real_data_ip)s</m></sim><br /><br />
                        <si>==========切换完成前，网络配置如下===========</si><br /><br />
                        <sa>原vlan ip 网卡配置如下:</sa><br />
                        <sim>原对外提供服务的业务网vlan ip:</sim>&nbsp;&nbsp;
                        <m>%(vlan_busi_ip)s</m><br />
                        <sim>原对外提供服务的数据网vlan ip:</sim>&nbsp;&nbsp;
                        <m>%(vlan_data_ip)s</m><br />
                        <sim>--------------------------------------------------------------------------------------</sim><br />
                        <sa>原vlan ip绑定的主机网卡配置如下:</sa><br />
                        <sim>原主机数据网&nbsp;网卡IP地址:&nbsp;<m>%(real_data_ip)s</m></sim><br />
                        <sim>原主机业务网&nbsp;网卡IP地址:&nbsp;<m>%(real_busi_ip)s</m></sim><br />
                        <sim>--------------------------------------------------------------------------------------</sim><br />
                        <sa>原未绑定vlan ip的备机网卡配置如下:</sa><br />
                        <sim>原未绑定备机数据网&nbsp;网卡IP地址:&nbsp;<m>%(s_real_data_ip)s</m></sim><br />
                        <sim>原未绑定备机业务网&nbsp;网卡IP地址:&nbsp;<m>%(s_real_busi_ip)s</m></sim><br /><br />
                        </body>
                        </html>
                        ''' % {'date_time':data['date_time'],'vlan_busi_ip':data['vlan_busi_ip'],'vlan_data_ip':data['vlan_data_ip'],'real_data_ip':data['real_data_ip'],'real_busi_ip':data['real_busi_ip'],'s_real_data_ip':data['s_real_data_ip'],'s_real_busi_ip':data['s_real_busi_ip']}
    elif 'vc' == tag:
        out_data = '''<!doctype html>
                        <html lang="en">
                         <head>
                          <meta charset="UTF-8">
                         </head>
                         <STYLE>
                            m {color:DeepPink ;text-align:center}
                            sa {color:MediumBlue   ;text-align:center}
                            si {font-size:16px}
                         </STYLE>
                         <body>
                        <p><b>
                        <si>vlan ip绑定完毕!<br /><br />
                        ==========vlan ip&nbsp;绑定完成后，配置如下===========</si><br /><br />
                        <si>绑定结束时间:</m>
                        <m>&nbsp;&nbsp;%(date_time)s</m><br />
                        <si>业务网vlan ip:</si>&nbsp;&nbsp;
                        <m>&nbsp;&nbsp;%(vlan_busi_ip)s </m><br />
                        <si>数据网vlan ip:</si>&nbsp;&nbsp;
                        <m>&nbsp;&nbsp;%(vlan_data_ip)s</m><br />
                        <si>vlan ip绑定的服务器IP地址:</si><br />
                        <m>&nbsp;&nbsp;服务器数据网网卡ip地址:&nbsp;%(real_data_ip)s&nbsp;/&nbsp;服务器业务网网卡ip地址:&nbsp;%(real_busi_ip)s</m><br />
                        <si>当前服务器类型:</si>
                        <sa>%(mc_name)s</sa><br />
                        <si>当前服务器所在机房:</si>
                        <sa>%(name)s</sa><br />
                        </body>
                        </html>
                        ''' % {'date_time':data['date_time'],'vlan_busi_ip':data['vlan_busi_ip'],'vlan_data_ip':data['vlan_data_ip'],'real_data_ip':data['real_data_ip'],'real_busi_ip':data['real_busi_ip'],'mc_name':data['mc_name'],'name':data['name']}

    return out_data
