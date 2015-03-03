# -*- coding: utf-8 -*-
#!/usr/bin/python
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib,os
import time
import my_lib

class Send_Email():

    def __init__(self, config):
        self.smtpserver = config['smtp_server']
        self.sender = config['sender']
        self.password = config['password']
        self.receiver = config['receiver']
        self.subject = config['subject']

        server = smtplib.SMTP()
        server.connect(self.smtpserver)

        try:
            server.login(self.sender,self.password)
            self._server = server
        except Exception,e:
            my_lib.writelog(my_lib.langage_data('output','42',str(e)),'e')

    def sendText_Content(self,content):
        '''
            发送文本文件的邮件内容
        '''
        userlist=[]

        msg = MIMEMultipart()

        msg.attach(MIMEText(content, 'html','gbk'))

        for user in self.receiver.split():
               userlist.append(user)


        msg['To'] = ';'.join(userlist)
        msg['Subject']=self.subject
        msg['From'] = self.sender
        msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')

        try:
             self._server.sendmail(self.sender,userlist,msg.as_string())
             return True
        except Exception,e:
              print e
              return False
        #print e
        #my_lib.writelog(my_lib.langage_data('output','43',str(e)),'e')


    def __del__(self):
        self._server.quit()
        self._server.close()
