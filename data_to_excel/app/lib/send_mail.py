# -*- coding: utf-8 -*-
#!/usr/bin/python
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os

from ConfigParser import ConfigParser
import time

class Send_Email():

    def __init__(self, config):
        self.smtpserver = config['smtp_server']
        self.sender = config['sender_mailbox']
        self.password = config['sender_password']
        self.receiver = config['reciver_mailbox']
        self.export_file = config['export_file']
        self.subject = config['subject']

        server = smtplib.SMTP()
        server.connect(self.smtpserver)

        try:
            server.login(self.sender,self.password)
            self._server = server
        except Exception,e:
            print "无法正常发送邮件，请查看配置!邮件异常,错误为: %s"  % str(e)

    def sendAttachMail(self):
        # 创建带附件的实例
        msg = MIMEMultipart()
        userlist=[]
        content = "打开excel的密码,请联系管理员!"
        mail_body = self.subject + "\n" + self.subject
        body = MIMEText(mail_body,'plain','utf-8')

        for user in self.receiver.split():
               userlist.append(user)
        msg['To'] = ';'.join(userlist)
        msg['Subject'] = self.subject
        msg['From'] = self.sender
        msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')

        msg.attach(body)

        att = MIMEText(open(r'%s' % self.export_file,'rb').read() ,'base64','gb2312')
        file_name = os.path.basename(self.export_file)
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment;filename="%s"' % file_name.decode('utf-8').encode('gb2312')
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

# mail_list = {
#         'sender_mailbox': 'test@juren.com',
#         'db_type': 'mysql',
#         'reciver_mailbox': 'xinjianguo@juren.com',
#         'smtp_server': 'smtp.juren.com',
#         'host': '172.16.1.196',
#         'db_name': 'tms_new',
#         'user': 'test',
#         'db_num': 'tms_100199273309',
#         'sender_password': 'jr123456',
#         'password': 'jr123456',
#         'port': '3307',
#         'subject': '2014-08-19_aaaaaa'
#         }
# mail_class = Send_Email(mail_list)
# mail_class.sendAttachMail()



