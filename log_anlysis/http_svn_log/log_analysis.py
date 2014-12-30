#!/usr/bin/env python
# coding=utf-8

#------------------------------------------------------
# Name:         Apache 日志分析脚本
# Purpose:      此脚本用来分析Apache的访问日志
# Version:      1.0
# Author:       xjg2010go
# Created:      2014-12-11
# Copyright:    (c) xjg2010go 2014
#------------------------------------------------------
import sys
import apache_log_parser
from  mysql_db_module.deal_data import Parse_Log,DataBase_Save_Log

import datetime,time

import pprint


class fileAnalysis(object):
    def __init__(self):
        self.report_detail_data = {}
        self.report_user_data = {}

    def init_data(self,host_info):
        '''
            初始化数据，host_info参数为字典,保存字典信息
        '''

        remote_ip = host_info['remote_ip']
        remote_user = host_info['remote_user']
        request_url = host_info['request_url']
        report_list = []

        if (remote_ip,remote_user) not in self.report_user_data:
            self.report_user_data[(remote_ip,remote_user)] = {}
        if (remote_ip,remote_user) not in self.report_detail_data:
            self.report_detail_data[(remote_ip,remote_user)] = {}

        report_list.append(host_info['status'])
        report_list.append('bytes')
        report_list.append('num')
        tempvalue = {}.fromkeys(report_list,1)
        tempvalue['bytes'] = host_info['request_bytes']
        self.report_user_data[(remote_ip,remote_user)][request_url] = report_list

        self.report_detail_data[(remote_ip,remote_user)][request_url] = tempvalue
        self.report_detail_data[(remote_ip,remote_user)][request_url]['from_time'] = host_info['from_time']
        self.report_detail_data[(remote_ip,remote_user)][request_url]['to_time'] = host_info['to_time']

        return {'report_user_data':self.report_user_data,'report_detail_data':self.report_detail_data}


    def get_to_detail_data_todic(self,logfile):
        '''
            按照小时切分日志,并生成对应的字典
        '''
        format_string = "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\""
        report_data = {} #存放所有逻辑数据
        time_temp = ''
        parser = apache_log_parser.make_parser(format_string)
        no_ip = ["::1"]
        no_bytes = ["-"]
        #按照小时切分日志
        cut_log_by_hour = 1
        time_status = 0


        for line in logfile:
            if len(line.strip()) > 0:
                logdata = parser(line)
                try:
                    if logdata['remote_host'] in no_ip:
                        continue
                    else:
                        report_data['remote_ip'] = logdata['remote_host']
                    report_data['remote_user'] = logdata['remote_user']
                    report_data['status'] = str(logdata['status'])

                    if logdata['request_url'].startswith("/svn/"):
                        report_data['request_url'] = logdata['request_url'].split('/')[2]
                    else:
                        report_data['request_url'] = logdata['request_url']

                    if logdata['response_bytes_clf'] in no_bytes:
                        continue
                    else:
                        report_data['request_bytes'] = logdata['response_bytes_clf']

                    datetimeobj = logdata['time_received_datetimeobj']

                except IndexError,e:
                    with open("/tmp/analysis_apache.log","w+") as f:
                        f.write(logdata)
                        f.write("\n")
                        f.close()
                    print "Error! Stop!",e
                    break


                if time_status == 0:
                    from_time = datetime.datetime.strptime(datetimeobj.strftime("%Y%m%d%H"),"%Y%m%d%H")
                    to_time = from_time + datetime.timedelta(hours = cut_log_by_hour)
                    time_status = 1

                report_data['from_time'] = from_time.strftime("%Y/%m/%d %H:00:00")
                report_data['to_time'] = to_time.strftime("%Y/%m/%d %H:00:00")

                if datetimeobj > to_time:
                    time_status = 0
                elif datetimeobj < from_time:
                    time_status = 0


                data = self.parse_log((report_data['remote_ip'],report_data['remote_user']),report_data)
                print time.strftime('%Y-%m-%d %A %X %Z',time.localtime(time.time()))
        return data


    def parse_log(self,ip_user,report_data):
            '''
                分析日志，返回值
                ip_user:(remote_ip,remote_user)
                report_data: {}
            '''
            request_url   = report_data['request_url']
            status        = report_data['status']
            request_bytes = report_data['request_bytes']

            if ip_user in self.report_user_data:
                if request_url in self.report_user_data[ip_user].keys():
                    if status in self.report_user_data[ip_user][request_url]:
                        status_num = int(self.report_detail_data[ip_user][request_url][status])
                        status_num = int(status_num) + 1
                        self.report_detail_data[ip_user][request_url][status] = status_num
                    else:
                        self.report_user_data[ip_user][request_url].append(status)
                        self.report_detail_data[ip_user][request_url][status] = 1

                    #访问次数
                    url_num = self.report_detail_data[ip_user][request_url]['num']
                    url_num = int(url_num) + 1
                    self.report_detail_data[ip_user][request_url]['num'] = url_num

                    #计算字节
                    sum_bytes = self.report_detail_data[ip_user][request_url]['bytes']
                    sum_bytes = int(sum_bytes) + int(request_bytes)
                    self.report_detail_data[ip_user][request_url]['bytes'] = sum_bytes
                else:
                    self.report_user_data = self.init_data(report_data)['report_user_data']
                    self.report_detail_data = self.init_data(report_data)['report_detail_data']
            else:
                #存放状态列表
                self.report_user_data = self.init_data(report_data)['report_user_data']
                self.report_detail_data = self.init_data(report_data)['report_detail_data']

            return self.report_detail_data


class Main():
    def __init__(self):
        self.host = "10.11.194.104"
        self.user = "test"
        self.passwd = "test"
        self.port = 3306
        self.db = "apache_log"

    def main(self):
        filename = sys.argv[1]
        fileAnalysis_obj = fileAnalysis()
        with open(filename,'r') as infile:
            data = fileAnalysis_obj.get_to_detail_data_todic(infile)
            infile.close()
        db_obj = DataBase_Save_Log(self.host,self.user,self.passwd,self.port,self.db)
        parse_data = Parse_Log(data)
        source_data = parse_data.parse_log_data()

        for sql in parse_data.gernalrate_sql(source_data):
            db_obj.insert_data(sql)


if __name__ == '__main__':
    main_obj = Main()
    main_obj.main()

