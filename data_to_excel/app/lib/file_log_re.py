# -*- coding: utf-8 -*-
#!/usr/bin/python
import os
import sys
import time
import atexit
from signal import SIGTERM

class Record_daemon():

    def __init__(self,stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def daemonize(self):
        sys.stdout.flush()
        sys.stdin.flush()
        sys.stderr.flush()

        si = file(self.stdin,'r')
        so = file(self.stdout,'a+')
        se = file(self.stdout,'a+',0)

        os.dup2(si.fileno(),sys.stdin.fileno())
        os.dup2(so.fileno(),sys.stdout.fileno())
        os.dup2(se.fileno(),sys.stderr.fileno())




