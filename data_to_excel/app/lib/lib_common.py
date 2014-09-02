# -*- coding: utf-8 -*-
#!/usr/bin/python

from ConfigParser import ConfigParser
import datetime
import gzip
import sys

class MyBaseClass(ConfigParser):

    def __init__(self,config):
        self.db_conf = {}
        self.export_conf = {}
        ConfigParser.__init__(self)
        self.config = config

    def set_db_value(self,db_data):
        for k,v in db_data.items():
            self.db_conf[k] = v
            setattr(self,k,v)

    #Get export data config value
    #file_conf: Options
    def export_get_single_value(self,one_option):
        args = {}
        self.read(self.config)
        options = self.options(one_option)
        for value in options:
            args[value] = self.get(one_option,value)
        return args

    #Get export data config value
    #file_conf: Options
    def export_get_value(self):
        args = {}
        args_list =[]
        self.read(self.config)
        sections = self.sections()
        for i in sections:
            options = self.options(i)
            for value in options:
                args[value] = self.get(i,value)
            args_list.append(args)
            args = {}
        return args_list

    #获取最小值
    def get_min_value(self):
        max = 100
        self.read(self.config)
        sections = self.sections()
        for i in sections:
            num = self.get_chars(i)
            if int(num) < int(max) :
                max = num
            else:
                pass
        char = self.get_numbers(max)
        return char


    #Get database config value
    #file_conf: the file of database information
    def db_get_value(self,file_conf):
        args = {}
        self.read(self.config)
        options = self.options(file_conf)
        for value in options:
            args[value] = self.get(file_conf,value)
        return args

    #接收数据库配置
    def recive_db(self,tag="",count=1):
        if tag == 'db':
            options = self.db_conf['db_name']+'_db_conf'
        elif tag == 'case':
            options = self.get_numbers(count)
        else:
            print "Tag is not exsit!Please input \'db\' or \'case\'!"
        try:
            if not self.has_section(options):
                self.add_section(options)
            for k,v in self.db_conf.items():
                self.set(options,k,v)
            return True
        except Exception,e:
            print e
            return False

    #写入配置文件
    def save_db(self,path=""):
        file_name = "%s%s" % (path,self.config)
        with open (file_name,'a+') as dbconf:
            self.write(dbconf)
        return file_name

    #获取编号
    def get_numbers(self,count):
        dic = {
           '1' : 'one',
           '2' : 'two',
           '3' : 'three',
           '4' : 'four',
           '5' : 'five',
           '6' : 'six',
           '7' : 'seven',
           '8' : 'eight',
           '9' : 'nine',
           '10': 'ten',
           '11': 'eleven'
        }

        return dic[str(count)]

           #获取编号
    def get_chars(self,chars):
        dic = {
           'one':'1',
           'two' : '2',
           'three' : '3',
           'four' : '4',
           'five' : '5',
           'six' : '6',
           'seven' : '7',
           'eight' : '8',
           'nine' : '9',
           'ten' : '10',
           'eleven' : '11',
           'twelve' : '12',
           'thirteen': '13',
           'fourteen': '14',
           'fifteen' : '15',
           'sixteen':'16',
           'seventeen' : '17',
           'eighteen' : '18',
           'nineteen' : '19',
           'twenty':'20'
        }

        return dic[str(chars)]
# if __name__ == "__main__":
#     filename = "../data_export.ini"
#     dbconfig = MyBaseClass(filename)
#     dbconfig.get_min_value()
