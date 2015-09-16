#!/usr/bin/python
# -*- coding: utf-8 -*-


from mylib.base import Init_Base
import deal_ssh,common_lib
import time

class Genenal_Puppet_config(Init_Base):
    '''
        生成puppet配置类
    '''
    def __init__(self,init_server_info,db_server_info):
        print init_server_info
        print db_server_info
        super(Genenal_Puppet_config, self).__init__(init_server_info,db_server_info)

    def genenal_host_config(self):
        '''
            生成puppet配置
        '''
        result = ""
        temp_str1,temp_str2 = "",""
        web_str,db_str = "",""


        for server_info in self.init_server_info: 
            host_ip =  server_info['client_server']['client_ip']
            group = server_info['client_server']['group']

            sql = "select host_name from server_info where host_data_ip = '%s' or host_busi_ip = '%s'"
            result = super(Genenal_Puppet_config, self).select_advanced(sql,host_ip,host_ip)
            if len(result) > 0:
                if group == "online_web" or group == "dev":
                    temp_str1 += ("\'"+result+"\""  + ",")
                elif group == "online_db" or group == "db":
                    temp_str2 += ("\'"+result+"\""  + ",")


        web_str = temp_str1[:-1]
     

        web_option_one = "fordev_user"
        web_option_two = "online_all"
        web_option_three = "bizop_sys"

        web_puppet_conf = '''node \"%s\" {\n   include %s\n   include %s\n   include %s\n}''' % (web_str,web_option_one,web_option_two,web_option_three)


        default_option_one = "for_monitor"
        default_option_two = "bizop_sys"

        default_puppet_conf = '''node "default" {\n   include %s\n   include %s\n   }''' % (default_option_one,default_option_two)

        return web_puppet_conf,default_puppet_conf

    def set_host_config(self,web_puppet_conf,default_puppet_conf,puppet_list):
        '''
            设置puppet配置在puppet server上面
        '''
        result = ""
        for serverinfo in puppet_list:
            server_ip = serverinfo['puppet_server_ip']
            remote_user = serverinfo['puppet_server_user']
            remote_pass = serverinfo['puppet_server_passwd']

            command = "mv /etc/puppet/manifests/site.pp /etc/puppet/manifests/site.pp.BAK;echo %s > /etc/puppet/manifests/site.pp;echo %s >> etc/puppet/manifests/site.pp" % (web_puppet_conf,default_puppet_conf)

            result = deal_ssh.remote_ssh_password_simple(server_ip,remote_user,remote_pass,command)
            if result:
                print "puppet server %s: update sucess!" % server_ip

def close_host_config(puppet_list):
    result = ""
    log_time = time.strftime("%Y_%m_%d",time.localtime())
    for serverinfo in puppet_list:
        server_ip = serverinfo['puppet_server_ip']
        remote_user = serverinfo['puppet_server_user']
        remote_pass = serverinfo['puppet_server_passwd']

        command = "mv /etc/puppet/manifests/site.pp /tmp/site.pp.%s;mv /etc/puppet/manifests/site.pp.BAK /etc/puppet/manifests/site.pp;" % log_time

        result = deal_ssh.remote_ssh_password_simple(server_ip,remote_user,remote_pass,command)
        if result:
            print "puppet server %s: delete sucess!" % server_ip

