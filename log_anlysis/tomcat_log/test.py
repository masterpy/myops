#!/usr/bin/env python
#coding=utf-8
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#from email.mime.image import MIMEImage
import time
mail_body='hello, this is the mail content'
mail_from='server_alarm@juren.com'
mail_to=['xinjianguo@juren.com','xjg2010go@163.com']
msg=MIMEMultipart()
msg['Subject']='this is the title'
msg['From']=mail_from
msg['To']=';'.join(mail_to)
msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')

body=MIMEText(mail_body)
msg.attach(body)

att = MIMEText(open(r'/tmp/10.0.2.15.out.log.gz','rb').read(),'base64','gb2312')
att["Content-Type"] = 'application/octet-stream'
att["Content-Disposition"] = 'attachment;filename="herb.tar.gz"'
msg.attach(att)

smtp=smtplib.SMTP()
smtp.connect('smtp.juren.com')
smtp.login('server_alarm@juren.com','jr123456')
smtp.sendmail(mail_from,mail_to,msg.as_string())
smtp.quit()
print 'ok'
