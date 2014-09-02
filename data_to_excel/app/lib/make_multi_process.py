# -*- coding: utf-8 -*-
#!/usr/bin/python
from multiprocessing import Pool
from db_core import MyDBClass
from export_core import MyExportClass
from file_log_re import Record_daemon

import sys,os,time
import threading
import Queue

class Consumer(threading.Thread):
    def __init__(self,queue=None):
        threading.Thread.__init__(self)
        self._queue = queue

    def run(self):
        while True:
            content = self._queue.get()
            if isinstance(content, str) and content == 'quit':
                break
        print 'Bye byes!'

def Make_process_class(export_class,item):
        #仅仅重定向输出
        export_class.deal_export_conf(item)

def Producer(data_export_file="",db_name="",process_num=""):
    # data = [{'title': 'first_data', 'sql_file': 'data/sql_dir/2014-08-20_tms_2233_first_data.sql', 'excel_data_dir': 'data/export_dir', 'filename': 'tms_2233_first_data.xlsx', 'db_name': 'tms', 'sn': 'one', 'jira_case': 'tms_2233', 'subject': '2014-08-20_first_data'}, {'title': 'second_data', 'sql_file': 'data/sql_dir/2014-08-20_tms_4455_second_data.sql', 'excel_data_dir': 'data/export_dir', 'filename': 'tms_4455_second_data.xlsx', 'db_name': 'tms', 'sn': 'two', 'jira_case': 'tms_4455', 'subject': '2014-08-20_second_data'}]
    database_name = db_name
    #加载数据源文件
    myexportclass = MyExportClass(data_export_file,database_name)
    #获取数据
    export_data = myexportclass.get_export_conf_value()
    queue = Queue.Queue()
    worker_threads = build_worker_pool(queue,int(process_num))
    start_time = time.time()
    #Add the urls to process
    for item in export_data:
        queue.put(Make_process_class(myexportclass,item))
    # Add the poison pillv
    for worker in worker_threads:
        queue.put('quit')
    for worker in worker_threads:
        worker.join()

    print 'Done! Time taken: {}'.format(time.time() - start_time)
    return myexportclass

#线程池
def build_worker_pool(queue, size):
    workers = []
    for _ in range(size):
        worker = Consumer(queue=queue)
        worker.start()
        workers.append(worker)
    return workers

