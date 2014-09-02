# -*- coding: utf-8 -*-
#---------------------------------------------------------
# Name:         Tomcat错误日志发送邮件脚本
# Purpose:      收集Tomcat异常日志并发送邮件
# Version:      1.0
# Author:       xjg
# EMAIL:        xinjianguo@juren.com
# Created:      2014-06-10
# Python：       2.7/2.4  皆可使用
#--------------------------------------------------------

#!/usr/bin/python
import re
import datetime
import sys
import pprint



class Tomcat_log_analysis():
        def __init__(self,time,file_buffer):
            self.time = int(time.split()[0])
            self.measure_time = time.split()[1]
            self.buffer = int(file_buffer)

        def parse_apache_date(self,days,hours):
            '''
                格式化时间
            '''
            year,month,day = days.split('-')
            hour, minute,second = hours.split(':')
            return datetime.datetime(int(year),int(month),int(day),int(hour),int(minute))


        def buffer_read(self,fd):
            '''
                利用缓冲读取数据,倒读数据
            '''
            buffer_r = self.buffer
            line = ''
            fd.seek(0,2)
            size = fd.tell()
            rem = size % buffer_r
            pos = max(0,(size - (buffer_r + rem)))
            while pos >= 0:
                fd.seek(pos,0)
                d = fd.read(buffer_r + rem)
                rem = 0
                pos -= buffer_r
                if "\n" in d:
                    for c in reversed(d):
                        if c != '\n':
                            line = c + line
                        else:
                            if line:
                                yield line
                            line = c
                else:
                    line = d +  line
            yield line


        def get_lastlog(self,srclog):
            '''
                截取最新日志
            '''
            LOG = srclog
            line = ""
            result = []
            now = datetime.datetime.now()
            if self.measure_time == "minutes":
                timedelta = datetime.timedelta(minutes=self.time)
            elif self.measure_time == "hours":
                timedelta = datetime.timedelta(hours=self.time)
            elif self.measure_time == "days":
                timedelta = datetime.timedelta(days=self.time)
            time_ago = now - timedelta
            with open (LOG,'r') as fd:
                    for line in self.buffer_read(fd):
                            time_p = re.compile(r'^[\w]+-[\d]+-[\d]+')
                            if time_p.findall(line):
                                splitd_line = line.split()
                                days = splitd_line[0]
                                hours = splitd_line[1].split(',')[0]
                                self.time_now = self.parse_apache_date(days,hours)
                                if time_ago > self.time_now:
                                       break
                            result.append(line)
            return result

        def deal_log(self,datalines,raw_log):
                '''
                        将最新日志处理后正序排列
                '''
                new_line = []
                for i in range(len(datalines)-1,-1,-1):
                        if i == 0:
                            time = datalines[i]
                        else:
                            new_line.append(datalines[i])
                with open(raw_log,'w') as fd:
                    for line in new_line:
                        fd.write(line)
                fd.close()


        def log_analysis(self,destlog):
            '''
                分析日志获取错误信息
            '''
            LOG = destlog
            line = ""
            self.new_line = ""
            result = []
            self.time_now = ""

            with open (LOG,'r') as fd:
                for line in fd:
                        time_p = re.compile(r'^[\w]+-[\d]+-[\d]+')
                    #    debug_p = re.compile(r'^java\.lang\.Exception\:\sDEBUG.*')
                        java_error = re.compile(r'(^java\.lang\.[\S]+)|(^org.apache.*)')
                        content_error = re.compile(r'(^[ \t]*at\s)')
                        if time_p.findall(line):
                                self.new_line = line
                        else:
                                if line:
                                    for i in java_error.findall(line):
                                            if i:
                                                result.append(self.new_line)
                                                result.append(line)
                                                self.new_line = ""
                                    if content_error.findall(line):
                                        result.append(line)
            return result


# def main():
#     cnf = "./mail_log.conf"

#     log = Tomcat_log_analysis()
#     datalines = log.get_lastlog(sys.argv[1])
#     log.deal_log(datalines,temp_log)
#     result = log.log_analysis(temp_log)
#     with open(error_log,'w') as fd:
#         for line in result:
#             if line:
#                 fd.write(line)
#     fd.close()

# main()



