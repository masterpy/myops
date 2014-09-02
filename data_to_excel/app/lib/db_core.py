# -*- coding: utf-8 -*-
#!/usr/bin/python

import MySQLdb
from lib_common import MyBaseClass
import os
import sys

class MyDBClass():
    def __init__(self,db_name="",path=""):
        if len(path) > 0:
            self.dbconf_filename = os.path.join(path,"db_conf.ini")
        else:
            self.dbconf_filename = "db_conf.ini"
        self.dbconfig = MyBaseClass(self.dbconf_filename)
        if len(db_name) > 0:
            conf = self.db_choose_value(db_name)
            self.conn = self.Connect_db(conf)

    #重新生成配置文件
    def gernal_dbconf_again(self,members):
        os.rename(self.dbconf_filename,'%s.bak' % self.dbconf_filename)
        self.init_db_conf(members)

    #返回和组合邮件参数
    def get_mail_info(self,subject,attach_file,db_name):
        conf = self.db_choose_value(db_name)
        args = self.dbconfig.db_get_value(conf)
        args['subject'] = subject
        args['export_file'] = attach_file
        return args

    def init_db_conf(self,members):
        db_conflist=[]
        if not os.path.exists(self.dbconf_filename):
            db_conf_default = {}
            if members > 0:
                for i in range(0,members):
                    db_name = raw_input("请输入数据库名称......").strip()
                    while True:
                        if  len(db_name.strip()) == 0:
                            db_name = raw_input("请输入数据库名称......").strip()
                        else:
                            break
                    db_conf_default = self.set_default_value(db_name)
                    self.dbconfig.set_db_value(db_conf_default)
                    if self.dbconfig.recive_db('db'):
                        print "数据库 %s 配置生成成功!" % db_name
                path = self.dbconfig.save_db('lib/')
                print "数据库保存配置成功!路径如下:当前目录:%s, 文件保存在:%s" % (os.getcwd(),path)
        else:
            print "数据库配置文件 %s 已存在。" % self.dbconf_filename
            sys.exit(1)

    def set_default_value(self,db_name):
        args = {
        'db_num':'tms_100199273309',
        'host':'10.0.199.27',
        'port':3309,
        'db_user':'test',
        'db_password':'test',
        'db_name':db_name,
        'db_type':'mysql',
        'sender_mailbox' : 'test@juren.com',
        'sender_mailbox_password' : 'jr123456',
        'reciver_mailbox' : 'test@juren.com',
        'smtp_server' : 'smtp.juren.com'
        }
        return args

    #Choose DataBase
    def db_choose_value(self,db_name):
        if db_name == "tms":
            db_conf = "tms_db_conf"
        elif db_name == "jurenlong":
            db_conf = "jurenlong_db_conf"
        elif db_name == "card":
            db_conf = "card_db_conf"
        else:
            print "Must be input db_name"
            return False
        return db_conf


    def check_db(self,args):
        try:
            conn = MySQLdb.connect(host=args['host'],port=args['port'],user=['user'],password=['password'],db=args['db_name'],charset='utf8')
        except Exception, e:
            print e
            return False
        return True


    def Connect_db(self,db_conf):
        args = {}
        args = self.dbconfig.db_get_value(db_conf)
        user = args['user']
        password = args['password']
        host = args['host']
        port = int(args['port'])
        db = args['db_name']
        charset = 'utf8'
        try:
            conn = MySQLdb.connect(host=host,port=port,user=user,passwd=password,db=db,charset=charset)
            return conn
        except Exception, e:
            print e
            sys.exit(1)


    def Query(self,sql_str="",tag=0):
        if tag == 0:
            self.cursor = self.conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
            self.cursor.execute(sql_str)
            returnData = self.cursor.fetchall()
            return returnData
        else:
            self.cursor.close()
            self.conn.close()


    def Status(self,tag):
        if tag == 1:
            return True
        else:
            return False


