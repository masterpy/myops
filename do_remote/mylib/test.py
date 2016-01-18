#!/usr/bin/python
# -*- coding: utf-8 -*-

import paramiko,os
import  deal_gernal_password



if __name__ == '__main__':
    newpass_cls =  deal_gernal_password.PassWorder()
    newpass = newpass_cls.gernal_password()
    print newpass
    encrypt_pass = newpass_cls.encrypt_password(newpass)
    print newpass_cls.decrypt_password(encrypt_pass)

 


# class Write_logger(object):
#     def __init__(self,logfile):
#         self.logfile = logfile

#     def write_log(self,string):
#         '''
#             记录日志
#         '''
#         logger = logging.getLogger('mylogger')
#         logger.setLevel(logging.INFO)
#         fh = logging.FileHandler(self.logfile)
#         fh.setLevel(logging.INFO)
#         fmt = '%(asctime)s %(filename)s %(levelname)s %(message)s'
#         formatter = logging.Formatter(fmt)
#         fh.setFormatter(formatter)
#         logger.addHandler(fh)
#         logger.info(string)

# if __name__ == '__main__':
#     A = Write_logger("test.log")
#     A.write_log("2016-1-12")