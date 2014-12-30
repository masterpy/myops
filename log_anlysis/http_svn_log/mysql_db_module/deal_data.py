#!/usr/bin/env python
# coding=utf-8
import MySQLdb
import pprint,time

#数据库相关操作
class DataBase_Save_Log(object):
    def __init__(self,db_host,db_user,db_passwd,db_port,db_name):
        self.db_host = db_host
        self.db_user = db_user
        self.db_passwd = db_passwd
        self.db_port = db_port
        self.db_name = db_name

    def connect_db(self):
        try:
            db_conn = MySQLdb.connect(host=self.db_host,user=self.db_user,passwd=self.db_passwd,port=self.db_port,db=self.db_name,connect_timeout=20)
            return db_conn
        except  MySQLdb.Error,e:
            print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])

    def get_cursor(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        return conn,cursor


    def insert_data(self,sql):
        '''
        接收所有数据
        '''
        conn,cursor = self.get_cursor()
        try:
            cursor.execute(sql)
            cursor.close()
            conn.commit()
            conn.close()
        except Exception,e:
            print e


class Parse_Log(object):
    def __init__(self,data):
        self.data = data
        self.tempdic = {}
        self.status = ['200','201','204','207','301','302','304','400','401','403','404','405','409','500']
        self.init_status()
        self.update_time = time.strftime('%Y-%m-%d-%H:%M',time.localtime())

    def init_status(self):
        '''
            初始化 状态码
        '''
        self.tempdic = {}.fromkeys(self.status,0)
        return self.tempdic

    def format_size(self,size):
        '''
            格式化流量单位
            计算流量的时候用到了右移的位运算符 除以1个1024，就是右移10位 >> 10 这就是把B转换为了KB
            除以 1024 * 1024 就是右移20位，这就把B转换为了MB，依次类推
        '''
        KB = 1024           #KB -> B  B是字节
        MB = 1048576        #MB -> B  1024 * 1024
        GB = 1073741824     #GB -> B  1024 * 1024 * 1024
        TB = 1099511627776  #TB -> B  1024 * 1024 * 1024 * 1024
        if size >= TB :
            size = str(size >> 40) + 'T'
        elif size < KB :
            size = str(size) + 'B'
        elif size >= GB and size < TB:
            size = str(size >> 30) + 'G'
        elif size >= MB and size < GB :
            size = str(size >> 20) + 'M'
        else :
            size = str(size >> 10) + 'K'
        return size

    def parse_log_data(self):
        '''
        将ip,user,repo 并入单字典
        '''
        all_list = []
        for ip_user,value in self.data.items():
            for repo,attitute in value.items():
                 attitute['ip'] = ip_user[0]
                 attitute['user'] = ip_user[1]
                 attitute['repo'] = repo
                 all_list.append(attitute)
        return all_list

    def gernalrate_sql(self,source_dic):
        '''
            生成sql语句，并返回
        '''
        status_dic = {}
        for one_data in source_dic:
            for key,value in one_data.items():
                if key == 'ip':
                    ip = value
                elif key == 'user':
                    user = value
                elif key == 'repo':
                    repo = value
                elif key == 'bytes':
                    traffic = self.format_size(int(value))
                elif key == 'num':
                    access_count = value
                elif key == 'from_time':
                    from_time = value
                elif key == 'to_time':
                    to_time = value
                else:
                    status_dic = self.get_status_total(key,value)
            self.init_status()

            sql = '''
                insert into log_analysis_detail (ip,user,repo,traffic,access_count,from_time,to_time,status_200,status_201,status_204,status_207,status_301,status_302,status_304,status_400,status_401,status_403,status_404,status_405,status_409,status_500,update_time) values ('%(ip)s','%(user)s','%(repo)s','%(traffic)s','%(access_count)s','%(from_time)s','%(to_time)s','%(status_200)s','%(status_201)s','%(status_204)s','%(status_207)s','%(status_301)s','%(status_304)s','%(status_400)s','%(status_401)s','%(status_403)s','%(status_404)s','%(status_404)s','%(status_405)s','%(status_409)s','%(status_500)s','%(update_time)s')
            ''' % {'ip':ip,'user':user,'repo':repo,'traffic':traffic,'access_count':access_count,'from_time':from_time,'to_time':to_time,'status_200':status_dic['200'],'status_201':status_dic['201'],'status_204':status_dic['204'],'status_207':status_dic['207'],'status_301':status_dic['301'],'status_304':status_dic['304'],'status_400':status_dic['400'],'status_401':status_dic['401'],'status_403':status_dic['403'],'status_404':status_dic['404'],'status_405':status_dic['405'],'status_409':status_dic['409'],'status_500':status_dic['500'],'update_time':self.update_time}

            yield sql.strip()

    def get_status_total(self,key,value = 0):
        '''
            统计状态码
        '''
        if key in self.status:
            self.tempdic[key] = value
        else:
            pass
        return self.tempdic





