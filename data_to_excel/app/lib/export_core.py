# -*- coding: utf-8 -*-
#!/usr/bin/python
import MySQLdb
from lib_common import MyBaseClass
from db_core import MyDBClass
import os,sys,xlsxwriter,gzip,time,tarfile,datetime
from send_mail import Send_Email


class MyExportClass():
    def __init__(self,filename="data_export.ini",db_name=""):
        self.filename = filename
        self.dbfile_dir = "lib"
        self.db_name = db_name
        self.dbconfig = MyBaseClass(self.filename)
        self.mydbclass = MyDBClass(self.db_name,self.dbfile_dir)
        if len(db_name) > 0:
            self.one_option = self.dbconfig.get_min_value() #获取export.ini 的首个选项配置
        self.process_num = 5 #定义线程的数量

    #重新生成配置文件
    def gernal_mailconf_again(self,members):
        os.rename(self.filename,'%s.bak' % self.filename)
        self.init_export_conf(members)

    #获取导出数据配置值
    def get_export_conf_value(self):
        args_list = {}
        args_list = self.dbconfig.export_get_value()
        return args_list

    #处理数据配置信息
    def deal_export_conf(self,item):

        mail_list = {}
        title = item['title']
        sql_file = item['sql_file']
        data_dir = "%s/%s/%s" % (item['excel_data_dir'],time.strftime("%Y%m%d"),item['jira_case'])
        filename = "%s.xlsx" % title
        if not os.path.exists("sql_dir"):
            os.makedirs("sql_dir")
        elif not os.path.exists(data_dir):
            os.makedirs(data_dir)
        else:
            pass
        if os.path.exists(sql_file):
              #得出sql语句
              sqldetail = self.get_sql_value(sql_file)
              #通过sql语句得出查询结果
              result = self.deal_sql(sqldetail,0)
              print result
              #写入excel
              self.deal_excel(data_dir,filename,result)
        else:
            print "%s is not exsit!sql文件不存在!" % sql_file

    #打包数据，清理数据并且发送邮件
    def tar_data(self,root_dir):
        args_list = {}
        args_list = self.dbconfig.export_get_single_value(self.one_option)
        data_dir =  "%s/%s" % (args_list['excel_data_dir'],time.strftime("%Y%m%d"))
        zip_password = args_list['zip_password']
        #压缩excel
        outfilename = self.deal_exported_file(data_dir,root_dir,zip_password)

        # #发送收件人邮箱
        mail_list = self.mydbclass.get_mail_info("%s-%s" % (time.strftime("%Y-%m-%d"),'导出数据'),outfilename,self.db_name)
        mail_class = Send_Email(mail_list)
        mail_class.sendAttachMail()


    #返回sql文件内容
    def get_sql_value(self,file_name):
        if os.path.exists(file_name):
            with open (file_name,'rb') as f:
                f.seek(-2,2)
                if f.read(1).strip() == ";":
                    pass
                else:
                    f.seek(0,0)
                    sqlstr = ""
                    for line in f.readlines():
                        line = line.strip("\n")
                        if line.startswith("#"):
                            pass
                        else:
                            sqlstr = sqlstr + " " + line
                    sqlstr = sqlstr + ";"
            return sqlstr
        else:
            print "%s is not exist!" % file_name

    #处理sql语句,并插入excel中
    def deal_sql(self,sql,tag):
#        mydbclass = MyDBClass(self.db_name,self.dbfile_dir)
        result = self.mydbclass.Query(sql,tag)
        return result

    #写入excel
    def deal_excel(self,data_dir,filename,data):
        list1 = []
        list2 = []
        list3 = []

        file_name = os.path.join(data_dir,filename)
        workbook = xlsxwriter.Workbook(file_name)
        worksheet = workbook.add_worksheet()
        # for i in data['field_names']:
        #     for key,value in i.items():
        #         if key in list1:
        #             pass
        #         else:
        #             list1.append(key)
        #         list2.append(value)
        #     list3.append(list2)
        #     list2 = []

        #添加列名
        red = workbook.add_format({'color': 'red','bold': True})

        i = 0
        for value in data['field_names']:
            #worksheet.write(0,i,value.deco  de('utf-8'))
            worksheet.write_rich_string(0,i,red,value.decode('utf-8'))
            i = i + 1
        j = 1
        col = 0
        #添加数值
        for row_data in data['returnData']:
            for col_data in row_data:
                if type(col_data) == datetime.datetime:
                    col_data = col_data.strftime("%Y-%m-%d %H:%M:%S")
                worksheet.write(j,col,col_data)
                col = col + 1
            j = j + 1
            col = 0


    #使用7z压缩excel文件
    def deal_exported_file(self,dir_name,root_dir,zip_password):
        import subprocess
        import shutil
        import re
        tempfile = ""
        tempdirname = "tempdir"
        temp_dir = os.path.join(root_dir,dir_name,tempdirname)

        templist = []
        new_filename = '%s.7z' % time.strftime("%Y%m%d")

        if os.path.exists(dir_name):
            #创建临时文件夹，删除临时文件夹中的文件
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            else:
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir)
                else:
                    os.remove(temp_dir)


            #转移文件到临时文件夹
            for r,d,f in os.walk(dir_name):
                for filename in f:
                    if len(filename) > 0:
                        if filename.split(".")[-1] == "xlsx":
                            templist.append(os.path.join(r,filename))

            for tempfile in templist:
                shutil.move(tempfile,temp_dir)

            tempfile = ""
            #拼接临时文件夹中的文件
            for name in os.listdir(temp_dir):
                  tempfile = tempfile + "    "+ name

            os.chdir(temp_dir)
            cmd = "%s %s %s%s %s %s" % ('7za','a','-p',zip_password,new_filename,tempfile)
            p1 = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True)
            output = p1.communicate()[0]


            #清空临时文件夹
            if os.path.exists(temp_dir):
                for tempfile in os.listdir(temp_dir):
                    if tempfile.split(".")[-1] == "xlsx":
                        os.remove(os.path.join(temp_dir,os.path.basename(tempfile)))
            last_new_filename = os.path.abspath(os.path.join(temp_dir,new_filename))
            return last_new_filename
        else:
            print "%s/%s文件不存在" % (dir_name,dir_name)
            sys.exit(1)


    #初始化导出数据的配置
    def init_export_conf(self,members):
        if not os.path.exists(self.filename):
            if members > 0:
                db_conf = {}
                dic_list = {}
                for i in range(0,members):
                    i = i + 1
                    numbers = self.dbconfig.get_numbers(i)
                    dic_list = self.print_input_value()
                    db_conf = self.set_default_value(dic_list,numbers)
                    #生成sql文件和目录
                    self.make_sqldir(db_conf['sql_file'])
                    self.dbconfig.set_db_value(db_conf)
                    if self.dbconfig.recive_db('case',i):
                        print "配置 %s 生成成功! " % numbers

            path = self.dbconfig.save_db()
            print "数据库保存配置成功!路径如下:当前目录:%s, 文件保存在:%s" % (os.getcwd(),path)
            print "==========================================================================="
            print "本次配置如下..............................................................."
            with open(path) as f:
                print f.read()
        else:
            print "%s 配置已存在，请移除!" % self.filename


    #生成sqldir文件
    def make_sqldir(self,file_path):
        dir_name = os.path.dirname(file_path)
        if os.path.exists(dir_name):
            pass
        else:
            os.makedirs(dir_name)
        with open(file_path,'w') as f:
            f.write("")
        f.close()



    #默认导出数据表
    def set_default_value(self,dic_list,numbers):
        args = {
                'sn':'%s' % numbers,
                'database_name':  dic_list['db_name'],
                'title':'%s' % dic_list['title'],
                'subject':"%s_%s" % (time.strftime("%Y-%m-%d"),dic_list['title']),
                'jira_case':dic_list['jira_case'],
                'sql_file':"data/sql_dir/%s_%s_%s.sql" % (time.strftime("%Y-%m-%d"),dic_list['jira_case'],dic_list['title']),
                'filename':"%s_%s.xlsx" % (dic_list['jira_case'],dic_list['title']),
                'excel_data_dir':'data/export_dir/',
                'zip_password' : 'jr123456'
                }
        return args

    #打印输入函数
    def print_input_value(self):
        try :
            db_name = raw_input("请输入数据库名称 \033[1;31;40m 名称必须与lib/db_conf.ini下的配置中的db_name必须一致\033[0m......").strip()
            while True:
                if  len(db_name.strip()) == 0:
                    db_name = raw_input("\033[1;31;40m 请输入数据库名称,与lib/db_conf.ini下的配置中的db_name必须一致\033[0m......").strip()
                else:
                    break

            jira_case = raw_input("请输入本次提案号\033[1;31;40m (例如:TMS_3322)\033[0m,请统一使用大写字母和下划线表示......").strip()
            while True:
                if  len(db_name.strip()) == 0:
                    jira_case = raw_input("请输入本次提案号 \033[1;31;40m (例如:TMS_3322)\033[0m,请统一使用大写字母和下划线表示......").strip()
                else:
                    break

            title = raw_input("请输入本次导出生成的文件名 \033[1;31;40m(例如:小班数据)\033[0m,请保持文件名唯一，为了区分方便......").strip()
            while True:
                if  len(db_name.strip()) == 0:
                    title = raw_input("请输入本次导出生成的文件名 \033[1;31;40m(例如:小班数据)\033[0m,请保持文件名唯一，为了区分方便......").strip()
                else:
                    break


            return {
            'db_name':db_name,
            'jira_case':jira_case,
            'title':title,
            }
        except KeyboardInterrupt:
            sys.exit(1)









