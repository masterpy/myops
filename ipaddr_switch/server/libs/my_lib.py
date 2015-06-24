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
import pprint
import getpass,re
import logging.handlers
from progressbar import AnimatedMarker,FormatLabel,ReverseBar,ProgressBar

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


    def ipFormatChk(self,ip_str):
        '''
            ip合法性检查
        '''
        pattern = r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"

        if re.match(pattern, ip_str):
            return True
        else:
            return False

    def timer_progress(self,e):
        '''
            进度条
        '''
        print "\n"
        widgets = ['Working: ', AnimatedMarker(),"  ||",FormatLabel('Processed:  %(elapsed)s s')]
        pbar = ProgressBar(widgets=widgets, maxval=20000).start()
        for i in range(20000):
            time.sleep(0.01)
            pbar.update(10*i+1)
            if e.is_set():
                return
        pbar.finish()
        sys.exit(1)

    def get_hostinfo_by_ip(self,url,real_ip,vlan_ip):
        '''
        依据ip地址，生成hostinfo 格式类似通过modename获取到的
        '''
        server_vertify_data = self.get_url_data(url)
        if not server_vertify_data:
            return False
        #pprint.pprint(server_vertify_data)
        if  server_vertify_data['success'] == 'true':
            for data in server_vertify_data['message']:
                if real_ip in data.values():
                    self.host_info['isvirtual'] = data.get('isxen')
                    self.host_info['service'] = "未配置"
                    self.host_info['mipbusi'] = data.get('busi_ip')
                    self.host_info['mipdata'] = data.get('data_ip')
                    self.host_info['mc'] = data.get('isxen')

                elif vlan_ip in data.values():
                    self.host_info['vipbusi'] = data.get('busi_ip')
                    self.host_info['vipdata'] = data.get('data_ip')
                    self.host_info['master_sn'] = data.get('serialid')
            return self.host_info
        writelog("模块不存在，无法获取信息!",'e')
        return False


    def get_host_info(self,url):
        '''
        依据模块获取主机配置信息
        '''
        num = 0
        server_vertify_data = self.get_url_data(url)
        
        if not server_vertify_data:
            return False

        if  server_vertify_data['success'] == 'true':
            if len(server_vertify_data['message']) <= 3 and len(server_vertify_data['message']) > 1:
                #只支持1主1备
                for value in server_vertify_data['message']:
                    self.host_info['isvirtual'] = value.get('isvirual')
                    self.host_info['service'] = "".join(value.get('service')) #列表

                    if value.get('type') == "0":
                        #0 表示备机
                        self.host_info['sipbusi'] = value.get('ipbusi')
                        self.host_info['sipdata'] = value.get('ipdata')
                        self.host_info['shostname'] = value.get('hostname')
                        self.host_info['slave_sn'] = value.get('serialid')
                        num = num + 1
                    elif value.get('type') == "1":
                        #1 表示主机
                        self.host_info['mipbusi'] = value.get('ipbusi')
                        self.host_info['mipdata'] = value.get('ipdata')
                        self.host_info['mhostname'] = value.get('hostname')
                        self.host_info['mc'] = value.get('isvirual')
                        self.host_info['master_sn'] = value.get('serialid')
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
                writelog("\033[1;31;40m**Error**\033[0m 非法参数，请重新输入!\n",'e')
                return False

        else:
            writelog("模块不存在，无法获取信息!",'e')
            return False


    def get_idc_name(self,real_ip):
        '''
            依据ip地址，获取idc名称
            busi_ip: 主机业务网网卡ip(非vlan ip)
        '''
        if real_ip is None:
            return False

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
            stdin,stdout,sterr = client.exec_command(command,timeout = 15)
            result = stdout.read()
            error  = sterr.read()
            client.close()

        except Exception,e:
            writelog(e,'e')
            sys.exit(1)
        else:
            return result,error


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
            writelog(e,'e')
            return False
        except urllib2.URLError,e:
            writelog(e,'e')
            return False
        except TypeError,e:
            writelog(e,'e')
            return False
        except simplejson.scanner.JSONDecodeError,e:
            writelog(e,'e')
            return False

    def update_bizmonitor(self,url):
        '''
        更新监控机
        '''
        server_data = self.get_url_data(url)

        if "success" in server_data:
            if server_data['success'] == 'true':
                return True
            else:
                writelog(server_data["message"],'e')
                return False
        else:
            writelog(server_data["message"],'e')
            return False

    def send_email(self,content):
        '''
            发送邮件
        '''
        conf_dir = os.path.join(os.path.split(__file__)[0])
        conf_file = "%s/%s" % (conf_dir,"mail.conf")
        mailconf = Get_conf(conf_file)
        maillist = mailconf.get_value()
        mail = send_mail.Send_Email(maillist)
        if mail.sendText_Content(content):
            return True
        else:
            return False



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



def writelog(string,tag):
    '''
    记录相关日志
    '''
    username = getpass.getuser()
    log_time = time.strftime("%Y_%m_%d",time.localtime())
    now_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0],'logs')

    if not os.path.exists(now_dir):
        os.makedirs(now_dir)

    log_file = "%(dir)s/%(local_time)s.log" % {'dir':now_dir,'local_time':log_time}

    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes = 1024*1024, backupCount=5)


    fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)


    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter_console = logging.Formatter('%(message)s')
    console.setFormatter(formatter_console)

    logger = logging.getLogger(username)

    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console)
        logger.setLevel(logging.DEBUG)

    if tag == 'i':
        logger.info(string)

    elif tag == 'e':
        logger.error(string)




def langage_data(src,tag,*args):
            if len(args) == 2:
                out_data_two = {
                '6' : '手工输入的:\n\nvlan ip信息如下:\n\n vlan ip的业务网地址: \033[1;32;40m %s\033[0m\n\n vlan ip的数据网地址: \033[1;32;40m %s\033[0m\n\n' % args,
                '7' : '主机即将绑定的:\n\nvlan ip信息如下:\n\n vlan ip的业务网地址: \033[1;32;40m %s\033[0m\n\n vlan ip的数据网地址: \033[1;32;40m %s\033[0m\n\n' % args,
                }
                print  out_data_two[tag]
                return out_data_two[tag]

            elif len(args) == 10:
                out_data_ten = {
                    '1' : '''主机信息如下:\n\n 服务器类型: \033[1;32;40m %s\033[0m;\n\n 服务器的业务网ip地址: \033[1;32;40m %s\033[0m  网络:  %s \n\n 服务器的数据网ip地址: \033[1;32;40m %s\033[0m  网络:  %s \n\n 服务器所在机房: \033[1;32;40m%s\033[0m\n\n vlan ip所在业务网状态: %s \n\n vlan ip所在数据网状态: %s \n\n vlan ip 配置如下: %s / %s \n\n''' % args,
                    '2' : '''备机信息如下:\n\n 服务器类型: \033[1;32;40m %s\033[0m;\n\n 服务器的业务网ip地址: \033[1;32;40m %s\033[0m  网络:  %s \n\n 服务器的数据网ip地址: \033[1;32;40m %s\033[0m  网络:  %s \n\n 服务器所在机房: \033[1;32;40m%s\033[0m\n\n vlan ip所在业务网状态: %s \n\n vlan ip所在数据网状态: %s \n\n vlan ip 配置如下: %s / %s \n\n''' % args,
                    '3' : '''bizop平台获取到的信息如下:\n\n 模块名称:\033[1;32;40m %s\033[0m;\n\n 服务器(主机)的业务网ip地址: \033[1;32;40m %s\033[0m\n\n 服务器(主机)的数据网ip地址: \033[1;32;40m %s\033[0m\n\n 服务器(备机)的业务网ip地址: \033[1;32;40m %s\033[0m\n\n 服务器(备机)的数据网ip地址: \033[1;32;40m %s\033[0m\n\n vlan ip配置信息:\033[1;32;40m %s/%s \033[0m\n\n %s %s %s''' % args

            }
                print  out_data_ten[tag]
                return out_data_ten[tag]




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
                            vs {color:Red;text-align:center}
                            sa {color:MediumBlue   ;text-align:center}
                            si {font-size:18px}
                            sim {font-size:14px}
                         </STYLE>
                         <body>
                        <p><b>
                        <si>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;服务器ip地址 切换完毕!</si><br /><br />
                        <si>切换结束时间:</m>
                        <m>%(date_time)s</m></si><br />
                        <si>操作人:</m>
                        <m>%(user)s</m></si><br />
                        <sim>**************************************************************************************</sim><br />*<br />
                        <si>*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;主机信息如下:</si><br />*<br />
                        <sim>* 主机IP信息: <m>%(m_busi_ip)s /</m>
                        <m>%(m_data_ip)s</m></sim><br />
                        <sim>* 对外提供服务的ip地址:</sim>
                        <sim><m>%(m_busi_ip)s /</m>
                        <m>%(m_data_ip)s</m></sim><br />
                        <sim>* 主机序列号: </sim>
                        <sim><m>%(m_sn)s</m></sim><br />
                        <sim>* 主机所在模块信息: <m>%(server_name)s</m></sim><br />*<br />
                        <sim>**************************************************************************************</sim><br />*<br />
                        <si>*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;备机信息如下:</si><br />*<br />
                        <sim>* 备机IP信息: <m>%(s_busi_ip)s /</m>
                        <m>%(s_data_ip)s</m></sim><br />
                        <sim>* 备机序列号: </sim>
                        <sim><m>%(s_sn)s</m></sim><br />
                        <sim>* 备机所在模块信息: <m>%(server_name)s</m></sim><br />*<br />
                        <sim>**************************************************************************************</sim><br /><br />
                        </body>
                        </html>
                        ''' % {'date_time':data['date_time'],'m_sn':data['master_sn'],'s_sn':data['slave_sn'],'m_busi_ip':data['mipbusi'],'m_data_ip':data['mipdata'],'s_busi_ip':data['sipbusi'],'s_data_ip':data['sipdata'],'server_name':data['service'],'user':data['user']}
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
                        <si>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;vlan ip地址 切换完毕!</si><br /><br />
                        <si>切换结束时间:</m>
                        <m>%(date_time)s</m></si><br />
                        <si>操作人:</m>
                        <m>%(user)s</m></si><br />
                        <sim>**************************************************************************************</sim><br />*<br />
                        <si>*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;主机信息如下:</si><br />*<br />
                        <sim>* 主机IP信息: <m>%(m_busi_ip)s /</m>
                        <m>%(m_data_ip)s</m></sim><br />
                        <sim>* 主机已绑定的vlan ip:</sim>
                        <sim><m>%(vlan_busi_ip)s /</m>
                        <m>%(vlan_data_ip)s</m></sim><br />
                        <sim>* 主机序列号: </sim>
                        <sim><m>%(m_sn)s</m></sim><br />
                        <sim>* 主机所在模块信息: <m>%(server_name)s</m></sim><br />*<br />
                        <sim>**************************************************************************************</sim><br />*<br />
                        <si>*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;备机信息如下:</si><br />*<br />
                        <sim>* 备机IP信息: <m>%(s_busi_ip)s /</m>
                        <m>%(s_data_ip)s</m></sim><br />
                        <sim>* 备机序列号: </sim>
                        <sim><m>%(s_sn)s</m></sim><br />
                        <sim>* 备机所在模块信息: <m>%(server_name)s</m></sim><br />*<br />
                        <sim>**************************************************************************************</sim><br /><br />
                        </body>
                        </html>
                        ''' % {'date_time':data['date_time'],'vlan_busi_ip':data['vipbusi'],'vlan_data_ip':data['vipdata'],'m_sn':data['master_sn'],'s_sn':data['slave_sn'],'m_busi_ip':data['mipbusi'],'m_data_ip':data['mipdata'],'s_busi_ip':data['sipbusi'],'s_data_ip':data['sipdata'],'server_name':data['service'],'user':data['user']}

    elif 'vc' == tag:
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
                        <si>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;vlan ip地址 配置完成!</si><br /><br />
                        <si>配置完成时间:</m>
                        <m>%(date_time)s</m></si><br />
                        <si>操作人:</m>
                        <m>%(user)s</m></si><br />
                        <sim>**************************************************************************************</sim><br />*<br />
                        <si>*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;主机信息如下:</si><br />*<br />
                        <sim>* 主机IP信息: <m>%(m_busi_ip)s /</m>
                        <m>%(m_data_ip)s</m></sim><br />
                        <sim>* 主机已绑定的vlan ip:</sim>
                        <sim><m>%(vlan_busi_ip)s /</m>
                        <m>%(vlan_data_ip)s</m></sim><br />
                        <sim>* 主机序列号: </sim>
                        <sim><m>%(m_sn)s</m></sim><br />
                        <sim>* 主机所在模块信息: <m>%(server_name)s</m></sim><br />*<br />
                        <sim>**************************************************************************************</sim><br /><br />
                        </body>
                        </html>
                        ''' % {'date_time':data['date_time'],'vlan_busi_ip':data['vipbusi'],'vlan_data_ip':data['vipdata'],'m_sn':data['master_sn'],'m_busi_ip':data['mipbusi'],'m_data_ip':data['mipdata'],'server_name':data['service'],'user':data['user']}

    return out_data
