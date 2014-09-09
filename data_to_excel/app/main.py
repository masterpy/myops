# -*- coding: utf-8 -*-
#!/usr/bin/python

from lib.db_core import MyDBClass
from lib.export_core import MyExportClass
from lib.file_log_re import Record_daemon
from optparse import OptionParser
import sys
import time
import os
from multiprocessing import Pool
from lib.make_multi_process import Consumer,Producer

DIRNAME = os.path.dirname(os.path.abspath(__file__))


def main():
#    usage = "usage: %prog [options] arg1 arg2"
    arg_list = {}
    parser = OptionParser()
    mydbclass = MyDBClass()
    logfile = "/tmp/exportlog.log"
    errorlog = "/tmp/exporterror.log"
    process_num = 1 #进程数
    myrecordlog = Record_daemon(stdout=logfile)
 #   myrecordlog.daemonize() #重定向描述符

    parser.add_option("-i","--init",action="store",dest="init_data",default="",help="初始化配置 -i db 初始化数据库配置 -i case 初始化提案配置，需要和-m 一起使用!".decode('utf-8'))
    parser.add_option("-c","--config",action="store",dest="load_data",default="",help="加载数据导出配置文件,需要和-s 一起使用".decode('utf-8'))
    parser.add_option("-g","--again",action="store",dest="gernal_data",default="",help="重新生成配置文件,-g db 重新生成数据库配置 -g case 重新生成提案配置".decode('utf-8'))
    parser.add_option("-s","--source",action="store",dest="source_db",default="",help="选择数据源字段,目前只支持 card,tms,jurenlong 后缀需要写成如下形式: -s card or -s tms or -s jurenlong".decode('utf-8'))
    parser.add_option("-m","--members",action="store",dest="members_db",default="",help="生成数据源数量或者导出数据源数量 和-i配合使用，不能单独使用!如 -i db -m 3 或者 -g db -m 3".decode('utf-8'))

    ( options,args ) =  parser.parse_args()

    #初始化数据
    if len(options.init_data) > 0 and len(options.members_db) > 0:
        if options.members_db.isdigit():
            members = int(options.members_db)
            if  options.init_data == "db":
                mydbclass.init_db_conf(members)
            elif  options.init_data == "case":
                myexportclass = MyExportClass()
                myexportclass.init_export_conf(members)
            else:
                print "Please input args like \"-i db\" or \" -i case\""
        else:
            print "-m args Must be a number!"

    #加载配置文件
    elif len(options.load_data) > 0 and len(options.source_db) > 0:
        db_name = options.source_db
        data_export_file = options.load_data
        #加载数据源文件
        myexportclass = Producer(data_export_file,db_name,process_num)
        myexportclass.tar_data(DIRNAME)

    #重新生成配置文件
    elif len(options.gernal_data) > 0 and len(options.members_db > 0):
        if len(args) > 1:
            if options.gernal_data == "db":
                mydbclass.gernal_dbconf_again(members)
            elif options.gernal_data == "case":
                myexportclass = MyExportClass()
                myexportclass.gernal_mailconf_again(members)
            else:
                print "Please input args like \"-i db\" or \" -i case\""
    else:
        parser.print_help()

main()
