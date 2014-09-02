# -*- coding: utf-8 -*-
#!/usr/bin/python
from library.gernal_init import Gernal_conf
from library.log_analysis_lib import Tomcat_log_analysis
from library.send_mail import Send_Email
import os
import sys
import time
import gzip
from optparse import OptionParser


class Tomcat_log():

    def __init__(self,config):
        self.config = config
        time_local = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        self.temp_log = "/tmp/%s.tmp.log" % time_local

    def set_default_value(self):
        '''
               设置配置文件默认值
        '''
        self.set_value = Gernal_conf(self.config)
        self.set_value.set_log_default_value()
        self.set_value.save()

    def get_log_name(self, log):

        file_log = log
        # 文件名含有gz的
        logfile = os.path.basename(file_log)
        # 日志路径
        logpath = os.path.dirname(file_log)
        # 文件名不含gz的
        log_name = '.'.join(logfile.split('.')[0:3])

        return {"logfile": logfile, "logpath": logpath, "log_name": log_name}

    def get_log_value(self):
        '''
                获取配置并分析日志文件,压缩分析结果
        '''


        confdic = {}  # 存放配置参数
        logdic = {}  # 存放日志配置参数
        conf = Gernal_conf(self.config)
        confdic = conf.get_value(self.config)
        errorlog_dic = self.get_log_name(confdic['error_log_file'])
        tomcat_log = confdic['tomcat_log']
        error_log = os.path.join(
            errorlog_dic['logpath'], errorlog_dic['log_name'])

        log = Tomcat_log_analysis(confdic['log_time'],confdic['buffer'])

        if os.path.exists(tomcat_log):
            datalines = log.get_lastlog(tomcat_log)
            log.deal_log(datalines, self.temp_log)
            result = log.log_analysis(self.temp_log)

        f_out = gzip.open(confdic['error_log_file'], 'wb')
        for line in result:
            if line:
                f_out.write(line)
        f_out.close()

        mail_send = Send_Email(confdic)
        mail_send.sendAttachMail()


def opts():
    parser = OptionParser(usage="usage %prog options")
    parser.add_option("-i", "--init",
                      dest="init",
                      default="-",
                      action="store",
                      help="初始化参数，生成配置文件")
    parser.add_option("-c", "--config",
                      dest="config",
                      default="mail.conf",
                      action="store",
                      help="指定配置文件")

    return parser.parse_args()


def print_help():
    print "Please input args like this:"
    print "First:  *****.py  -i example.conf"
    print "Second: *****.py  -c example.conf"
    print "Help:   *****.py -h"


if __name__ == "__main__":
    options, args = opts()
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    dir_name = os.getcwd()

    config_file = os.path.join(dir_name, options.config)
    tomcat_log = Tomcat_log(config_file)
    if sys.argv[1] == "-c":
        if os.path.exists(config_file):
            tomcat_log.get_log_value()
        else:
            print "配置文件不存在!"
    elif sys.argv[1] == "-i":
        tomcat_log.set_default_value()
