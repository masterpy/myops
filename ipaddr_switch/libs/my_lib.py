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
        self.host_info = {}.fromkeys(['iptype','ipbusi','ipdata','hostname','isvirtual','stype','sipbusi','sipdata','shostname','mtype','mipbusi','mipdata','mhostname','mc','vipbusi','vipdata'],None)

    #检查是否符合切换要求
    def check_data(self,hjson,isvlanip):
        x = t = s = 0
        for i in hjson['data']:
            if i.get('iptype') == "0":
                x = x + 1
            if i.get('iptype') == "1":
                t = t + 1
            if i.get('iptype') == "2":
                s = s + 1
        if x != 1 or t != 1 or s != int(isvlanip):
            print x,t,s
            return False
        return True

    def get_vlan_ip(self,url):
        '''
            获取VLAN IP
        '''
        validate_url = url
        #调用bizmonitor接口，获取服务IP等信息
        if len(validate_url) > 0:
            server_vertify_data = self.get_url_data(validate_url)
            if not server_vertify_data:
                return False
        if server_vertify_data['success'] == 'true':
            return True
        else:
            return False

    def get_host_id(self,url):
        '''
        获取主机id
        '''
        sn_api_url = url
        #调用bizmonitor接口，获取服务IP等信息
        if len(sn_api_url) > 0:
            server_vertify_data = self.get_url_data(sn_api_url)
            if not server_vertify_data:
                return False

        if len(server_vertify_data['data']) > 0:
            for i in server_vertify_data['data']:
                if 'id' in i:
                   self.host_id['id'] = i.get('id')
                if 'isvlanip' in i:
                   self.host_id['is_vlanip'] = i.get('isvlanip')
        else:
            writelog(langage_data('output','45'),'e')
            return False

        return   self.host_id

    def get_host_info(self,url,host_id):
        '''
        获取模块配置信息
        '''
        id_api_url = url

        if self.host_id['id']:
            server_vertify_data = self.get_url_data(id_api_url)
            if not server_vertify_data:
                return False

        if not self.check_data(server_vertify_data,self.host_id['is_vlanip']):
            writelog(langage_data('output','20'),'e')
            return False

        for value in server_vertify_data['data']:
            self.host_info['iptype'] = value.get('iptype')
            self.host_info['isvirtual'] = value.get('isvirtual')

            if self.host_info['iptype'] == "0":
                self.host_info['stype'] = value.get('iptype')
                self.host_info['sipbusi'] = value.get('ipbusi')
                self.host_info['sipdata'] = value.get('ipdata')
                self.host_info['shostname'] = value.get('hostname')

            elif self.host_info['iptype'] == "1":
                self.host_info['mtype'] = value.get('iptype')
                self.host_info['mipbusi'] = value.get('ipbusi')
                self.host_info['mipdata'] = value.get('ipdata')
                self.host_info['mhostname'] = value.get('hostname')
                self.host_info['mc'] = value.get('isvirtual')

            elif self.host_info['iptype'] == "2":
                self.host_info['vipbusi'] = value.get('ipbusi')
                self.host_info['vipdata'] = value.get('ipdata')

        return  self.host_info

    def get_ip_value(self,real_ip,vlan_ip=""):
        '''
            依据输入的ip地址，判断Ip是否合法，并返回对应的Ip地址
            real_ip: 真实网卡ip地址
            vlan_ip: vlan ip地址
        '''
        if len(real_ip) == 0:
            return False

        try:
            #获取真实物理网卡地址
            real_ip_net = ".".join(IP(real_ip).strNormal().split('.')[:-2])
            real_ip_add = ".".join(IP(real_ip).strNormal().split('.')[2:])
            #获取vlan ip网卡地址
            if len(vlan_ip) > 0:
                vlan_ip_net = ".".join(IP(vlan_ip).strNormal().split('.')[:-2])
                vlan_ip_add = ".".join(IP(vlan_ip).strNormal().split('.')[2:])

        except ValueError,e:
            writelog(langage_data('output','46'),'e')
            return False

        self.ip_pool = {}

        #获取ip所在机房，得到字典，如:{'idc':'zw','name':'新兆维','data_ip':'10.136','busi_ip':'10.146'}
        for pool in self.iplists:
            for key,value in pool.items():
                if 'data_ip' == key:
                    if len(vlan_ip) > 0:
                        if real_ip_net == value and vlan_ip_net == value:
                            self.ip_pool = pool
                    else:
                        if real_ip_net == value:
                            self.ip_pool = pool

        if len(self.ip_pool) > 0:
            self.ip_pool['real_data_ip'] = ".".join((self.ip_pool['data_ip'],real_ip_add))
            self.ip_pool['real_busi_ip'] = ".".join((self.ip_pool['busi_ip'],real_ip_add))
            if len(vlan_ip) > 0:
                self.ip_pool['vlan_data_ip'] = ".".join((self.ip_pool['data_ip'],vlan_ip_add))
                self.ip_pool['vlan_busi_ip'] = ".".join((self.ip_pool['busi_ip'],vlan_ip_add))
                return self.ip_pool
            else:
                return self.ip_pool
        else:
            writelog(langage_data('output','46'),'e')
            return False


    def ip_check(self,ipaddr):
        ret = os.system("ping -c 2 " + ipaddr + "> /dev/null")
        if ret == 0:
                return True
        else:
                return False

    def ssh_cmd_2(self,ip,command):
        port = 22
        username = 'root'
        passwd = "pengzhi"
        #know_host = "/User/xinjianguo/.ssh/known_hosts"
        try:
            c = paramiko.SSHClient()
            c.load_system_host_keys()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            paramiko.util.log_to_file("t_ssh.log")
            c.connect(ip, 22, 'root',passwd)
            stdin, stdout, stderr = c.exec_command(command)
            result = stdout.read()
            print stderr.read()
            print stdout.read()
            c.close()

            return result
        except Exception,e:
            writelog(langage_data('output','16',e),'e')

    def ssh_cmd(self,ip,command):
        port = 22
        username = 'root'
        key_file = "/root/.ssh/authorized_keys"
        know_host = "/root/.ssh/known_hosts"
        #know_host = "/User/xinjianguo/.ssh/known_hosts"
        try:
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.load_system_host_keys(know_host)
            s.connect(ip,port,username,key_file)
            stdin,stdout,sterr = s.exec_command(command,timeout = 20)
            result = stdout.read()
            s.close()
            return result
        except Exception,e:
            writelog(langage_data('output','16',e),'e')

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
            writelog(langage_data('output','17',e),'e')
            return False
        except urllib2.URLError,e:
            writelog(langage_data('output','18',e),'e')
            return False
        except TypeError,e:
            writelog(langage_data('output','19'),'e')
            return False
        except simplejson.scanner.JSONDecodeError,e:
            writelog(langage_data('output','19'),'e')
            return False

    def update_bizmonitor(self,url):
        '''
        更新监控机
        '''
        writelog(langage_data('output','26'),'i')
        server_data = self.get_url_data(url)

        if "success" in server_data:
            if server_data['success'] == 'true':
                writelog(langage_data('output','27'),'i')
                return True
            else:
                writelog(langage_data('output','28',server_data["message"]),'i')
                return False
        else:
            writelog(langage_data('output','28',server_data["message"]),'i')
            return False

    def switch_service_ip(self,mc,master_data_ip,slave_data_ip,data_vip,busi_vip):
        '''
          切换主机和备机vip以及主机备机的ip;
          master_data_ip:主机的数据网ip
          slave_data_ip:备机的数据网ip
          data_vip: 数据网的vlan ip
          busi_vip: 业务网的vlan ip
        '''
        writelog(langage_data('output','39'),'i')
        svip_list = [data_vip,busi_vip]
        if len(svip_list) > 1:
            if self.ip_check(slave_data_ip):
                if self.ip_check(data_vip) and self.ip_check(busi_vip):
                    '''
                    删除需要切换的主机路由
                    '''
                    writelog(langage_data('output','31'),'i')
                    for ip in svip_list:
                        writelog(langage_data('output','32',ip),'i')
                        cmd = "biztech-vlan -m %s -p %s -o del"%(mc,ip)
                        ret = self.ssh_cmd(master_data_ip,cmd)
                        os.system("sleep 5")
                        if self.ip_check(ip):
                            writelog(langage_data('output','33',ip),'i')
                            return False

                    for ip in svip_list:
                        writelog(langage_data('output','34',ip),'i')
                        cmd = "biztech-vlan -m %s -p %s -o add"%(mc,ip)
                        self.ssh_cmd(slave_data_ip,cmd)
                        os.system("sleep 5")

                    cmd = "biztech-vlanstart.sh"
                    for i in range(2):
                        self.ssh_cmd(slave_data_ip,cmd)
                        os.system("sleep 3")

                    if self.ip_check(data_vip):
                        if self.ip_check(busi_vip):
                            return True
                        else:
                            writelog(langage_data('output','35',busi_vip),'i')
                            return False
                    else:
                        writelog(langage_data('output','36',busi_vip),'i')
                        return False
        else:
            writelog(langage_data('output','30',slave_data_ip),'e')
            return False


    def switch_ip(self,mhostname,shostname,master_data_ip,master_busi_ip,slave_data_ip,slave_busi_ip):
        '''
          切换主机和备机ip;
          mhostname:主机的hostname
          shostname:备机的hostname
          master_busi_ip:主机的业务网ip
          master_data_ip:主机的数据网ip
          slave_busi_ip:备机的业务网ip
          slave_data_ip:备机的数据网ip
        '''
        writelog(langage_data('output','39'),'i')
        bash_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0],'bash_scripts')
        if self.ip_check(slave_data_ip):
            #需要切换的主机网络正常
            if self.ip_check(master_data_ip) :
                if self.ssh_check(master_data_ip):
                    cmd = "bash %(bash_dir)s/switch.sh %(opt)s %(mhostname)s %(shostname)s %(master_data_ip)s %(master_busi_ip)s %(slave_data_ip)s %(slave_busi_ip)s" % {'bash_dir':bash_dir,'opt':"ms",'mhostname':mhostname,'shostname':shostname,'master_data_ip':master_data_ip,'master_busi_ip':master_busi_ip,'slave_data_ip':slave_data_ip,'slave_busi_ip':slave_busi_ip}
                    status,result = commands.getstatusoutput(cmd)
                    if not status:
                        return True
                    else :
                        writelog(langage_data('output','4',master_data_ip,result),'e')
                        return False
                else:
                    writelog(langage_data('output','29',master_data_ip),'e')
                    return False
            #需要切换的网络主机不正常
            else:
                cmd = "bash %(bash_dir)s/switch.sh %(opt)s %(mhostname)s %(shostname)s %(master_data_ip)s %(master_busi_ip)s %(slave_data_ip)s %(slave_busi_ip)s" % {'bash_dir':bash_dir,'opt':"ms",'mhostname':mhostname,'shostname':shostname,'master_data_ip':master_data_ip,'master_busi_ip':master_busi_ip,'slave_data_ip':slave_data_ip,'slave_busi_ip':slave_busi_ip}
                status,result = commands.getstatusoutput(cmd)
                if not status:
                    return True
                else :
                    writelog(langage_data('output','5',master_data_ip,result),'e')
                    return False
        else:
            writelog(langage_data('output','30',master_data_ip),'e')
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
                '1':'请输入需要配置的VLAN的服务器的\033[1;32;40mip地址，eth0,eth1均可 \033[0m 均可. 退出请输入Q >> %s' % ",".join(args),
                '2':'输入要为此服务模块配置\033[1;32;40m的VLANIP,业务网和数据网均可! \033[0m >> %s' % ",".join(args),
                '4':'\033[1;32;40m 请确认以上信息是否正确，是否进行IP绑定?确认，请输入(y/Y)，退出，请输入(n/N) \033[0m  >> %s ' % ",".join(args),
                '5':'请输入要切换的服务 \033[1;32;40m 模块名称 \033[0m,退出请输入Q >> %s' % ",".join(args),
                '6':'请确认是否进行IP切换[Y/N] >> %s' % ",".join(args),
                '7':'该模块没有vlan ip,请确认是否进行IP切换[Y/N] >> %s' % ",".join(args),
                '8':'请确认以上信息是否正确[Y/N] >> %s' % ",".join(args),
                '9':'为保证切换顺利，请输入需要切换的主机IP或者备机IP,退出请输入Q或q >> %s' % ",".join(args)
            }
            return input_data[tag]

        if src == "output":
            if len(args) <= 1:
                out_data_one = {
                    '1':'\033[1;32;40m 正在校验这些ip地址请耐心等待！\033[0m........................................',
                    '2':'{} \033[1;31;40m 是非法ip地址 \033[0m'.format(args),
                    '3':'当前VLANIP已配置在其他机器中，换个IP吧',
                    '4':'权限未开通，请联系系统管理员!',
                    '5':'校验结果不匹配!请重新输入.',
                    '6':'正在检查这些ip地址是否已使用请耐心等待！....................................',
                    '7':'  机器类型:\033[1;32;40m 实体机 \033[0m',
                    '8':'  机器类型:\033[1;32;40m 虚拟机 \033[0m',
                    '9':'正在配置数据网IP: \033[1;32;40m {} \033[0m,请等待......'.format(args),
                    '10':'正在配置业务网IP: \033[1;32;40m {} \033[0m,请等待......'.format(args),
                    '11':'正在删除多余路由,\033[1;31;40m 请勿中断,删除中\033[0m................',
                    '12':'退出配置！.....................',
                    '13':'\033[1;32;40m IP配置完毕 \033[0m,请将VLAN录入bizmonitor',
                    '14':'\033[1;31;40m VLAN绑定失败，请联系系统管理员 \033[0m',
                    '15':'\033[1;31;40m {} \033[0m. 请重新输入.'.format(args),
                    '16':'\033[1;31;40m Error! \033[0m ssh 认证失败，中控机无法登陆该机器，请配置ssh互信!错误如下: {}'.format(args),
                    '17':'服务器端响应失败,返回状态码: \033[1;31;40m {} \033[0m'.format(args),
                    '18':'无法到达服务器，网络不通，原因: {}'.format(args),
                    '19':'验证失败，该服务器没有相关接口权限。请联系开发管理员。',
                    '20':'此服务模块不具备切换条件，请重新输入!',
                    '21':'要切换的服务器信息如下 >> ',
                    '22':'  \033[1;31;40m当前主机\033[0m的hostname:\033[1;32;40m %s \033[0m' % ",".join(args),
                    '23':'  \033[1;31;40m备用主机\033[0m的hostname:\033[1;32;40m %s \033[0m'% ",".join(args),
                    '24':'\033[1;32;40m IP切换完毕,请等待20秒后尝试登录 \033[0m，如无法访问请联系系统管理员',
                    '25':'\033[1;31;40m IP切换失败，\033[0m 请联系系统管理员',
                    '26':'正在将新配置更新bizmonitor中.........',
                    '27':'bizmonitor 配置更新成功!',
                    '28':'bizmonitor 配置更新失败!原因如下: \n {}'.format(args),
                    '29':'主机 \033[1;32;40m {} \033[0m 通过ssh 无法正常登陆，无法执行操作切换ip,请联系管理员!'.format(args),
                    '30':'备机 \033[1;32;40m {} \033[0m 网络无法ping通。'.format(args),
                    '31':'正在进行IP切换....请耐心等待.',
                    '32':'正在释放主机 vlan 服务IP: \033[1;32;40m {}. \033[0m'.format(args),
                    '33':'主机IP: \033[1;32;40m {} \033[0m 无法删除路由，请重新确认，并联系系统管理员'.format(args),
                    '34':'正在配置备机 Vlan 服务IP: \033[1;32;40m {} \033[0m'.format(args),
                    '35':'业务网vlan ip \033[1;32;40m {} \033[0m 网络无法ping通，切换失败!'.format(args),
                    '36':'数据网vlan ip \033[1;32;40m {} \033[0m 网络无法ping通，切换失败!'.format(args),
                    '37':'没有相关权限.请联系管理员.',
                    '38':'输入参数不正确或者无法读取输入参数导致，请联系系统管理员.',
                    '39':'\033[1;31;40m 正在切换ip地址，请勿中断！\033[0m ....................................',
                    '40':'##############################\033[1;32;40m 切换 vlan ip \033[0m ##############################',
                    '41':'############################## \033[1;32;40m 切换 网卡ip \033[0m ##############################',
                    '42':'无法正常发送邮件，请查看配置!邮件异常,错误为: {}'.format(args),
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
                    '53':'\033[1;32;40m 邮件已成功发送,请查收邮件\033[0m'
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
                }
                print  out_data_two[tag]
                return out_data_two[tag]

            elif len(args) == 4:
                out_data_four = {
                '1' : 'Ip地址非法，请重新输入，其中 vipbusi是\033[1;32;40m %s \033[0m, sipbusi是\033[1;32;40m %s \033[0m,mipbusi是 \033[1;32;40m %s \033[0m .原因如下: \n %s' %  args,
            }
                print  out_data_four[tag]
                return out_data_four[tag]
            elif len(args) == 6:
                out_data_six = {
                    '1' : '''请确认以下信息:\n 服务器类型: \033[1;32;40m %s\033[0m;\n 服务器的业务网ip地址: \033[1;32;40m %s\033[0m;\n 服务器的数据网ip地址: \033[1;32;40m %s\033[0m;\n 已经绑定的业务网vlan ip地址: \033[1;32;40m%s\033[0m;\n 已经绑定的数据网vlan ip地址: \033[1;32;40m%s\033[0m;\n 服务器所在机房: \033[1;32;40m%s\033[0m;\n.\n''' % args
            }
                print  out_data_six[tag]
                return out_data_six[tag]

            elif len(args) == 8:
                out_data_eight = {
                    '1' : '''请确认以下信息:\n 服务器类型: \033[1;32;40m %s\033[0m;\n 服务器的业务网ip地址: \033[1;32;40m %s\033[0m;\n 服务器的数据网ip地址: \033[1;32;40m %s\033[0m;\n 即将绑定的业务网vlan ip地址: \033[1;32;40m%s\033[0m;\n 即将绑定的数据网vlan ip地址: \033[1;32;40m%s\033[0m;\n 服务器所在机房: \033[1;32;40m%s\033[0m;\n vlan ip 将绑定在\033[1;33;40m%s/%s\033[0m; 这台服务器上,请仔细确认.\n\n \033[1;31;40m警告!vlan ip绑定错误将导致网络故障或网络不能冗余等严重问题，请务必谨慎操作。\033[0m\n''' % args,
            }
                print  out_data_eight[tag]
                return out_data_eight[tag]

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
