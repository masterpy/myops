# -*- coding: utf-8 -*-
#!/usr/bin/python
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os
from gernal_init import Gernal_conf
from ConfigParser import ConfigParser
import time

class Send_Email():

    def __init__(self, config):
        self.smtpserver = config['smtpserver']
        self.sender = config['sender']
        self.password = config['password']
        self.receiver = config['receiver']
        self.log_file = config['error_log_file']
        self.subject = config['subject']

        server = smtplib.SMTP()
        server.connect(self.smtpserver)

        try:
            server.login(self.sender,self.password)
            self._server = server
        except Exception,e:
            print "无法正常发送邮件，请查看配置!邮件异常,错误为: %s"  % str(e)

    def sendAttachMail(self):
        userlist=[]
        mail_body = self.subject
        body = MIMEText(mail_body)

        # 创建带附件的实例
        msg = MIMEMultipart()

        for user in self.receiver.split():
               userlist.append(user)
        msg['To'] = ';'.join(userlist)
        msg['Subject']=self.subject
        msg['From'] = self.sender
        msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')

        msg.attach(body)

        att = MIMEText(open(r'%s' % self.log_file,'rb').read() ,'base64','gb2312')
        file_name = os.path.basename(self.log_file)
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment;filename="%s"' % file_name
        msg.attach(att)


        try:
             self._server.sendmail(self.sender,userlist,msg.as_string())
        except Exception,e:
              print str(e)
              return False

        print "邮件发送完毕,ok!~~~~~~~"


    def __del__(self):
        self._server.quit()
        self._server.close()

# class Test_mail(ConfigParser):
#     def __init__(self,config):
#         '''
#             必须初始化ConfigParser类，否则无法获取section
#         '''
#         ConfigParser.__init__(self)
#         self.config = config

#     def get_value(self):
#         conf = Gernal_conf(self.config)
#         confdic = conf.get_value(self.config)
#         mail_send = Send_Email(confdic)
#         mail_send.sendAttachMail()


# if __name__ == "__main__":
#       test = Test_mail('/Volumes/share_folder_web1/python/fabric_example/tomcat_log/mail.conf')
#       test.get_value()



