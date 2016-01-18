#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging

def write_log(string):
    '''
        记录日志
    '''
    logfile = "/usr/local/src/init.log"
    logger = logging.getLogger('mylogger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.INFO)
    fmt = '%(asctime)s %(filename)s %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info(string)
