#!/usr/bin/python
# -*- coding: utf-8 -*-
import random
import re,time,string,logger

import base64
import hashlib
from mylib.base import Init_Base

from Crypto import Random
from Crypto.Cipher import AES

class AESCipher(object):
    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(AESCipher.str_to_bytes(key)).digest()

    @staticmethod
    def str_to_bytes(data):
        u_type = type(b''.decode('utf8'))
        if isinstance(data, u_type):
            return data.encode('utf8')
        return data

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * AESCipher.str_to_bytes(chr(self.bs - len(s) % self.bs))

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

    def encrypt(self, raw):
        raw = self._pad(AESCipher.str_to_bytes(raw))
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw)).decode('utf-8')

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

class PassWorder(Init_Base):
    '''
        修改密码类
    '''
    def __init__(self,db_server_info,ssh_con):
        '''
            初始化
        '''
        super(PassWorder,self).__init__(db_server_info)
        self.ssh_con = ssh_con


    def gernal_password(self):
        '''
            生成密码
        '''
        def id_generator(size=6, chars=string.ascii_uppercase + string.digits+'!@%^&*()'):
            return ''.join(random.choice(chars) for _ in range(size))
        password = id_generator(14)
        return password


    def encrypt_password(self,new_password):
        '''
            保存密码至mysql数据库
            data_list: 主机信息列表
        '''
        key = "6QqnsHGibwaGt4jkZxGmBpeYngNnqMqJ"
        decryptor = AESCipher(key=key)
        plaintext = decryptor.encrypt(new_password)

        return plaintext

    def decrypt_password(self,new_password):
        '''
            解密
        '''
        key = "6QqnsHGibwaGt4jkZxGmBpeYngNnqMqJ"
        new_cipher = AESCipher(key=key)
        plaintext = new_cipher.decrypt(new_password)
        return  plaintext

    def save_password(self,host_ip,raw_pass,encrypt_pass):
        '''
            保存密码
        ''' 
        user = "root"
        _command = 'echo \"%s\" | passwd %s --stdin' % (raw_pass,user)
        self.ssh_con.do_remote_by_passwd_exec(_command)

        #保存密码临时文件
        f = open('/tmp/machine.list.pass','a+')
        f.write(host_ip)
        f.write(",")
        f.write(encrypt_pass)
        f.write("\n")
        f.close()

        #保存密码到数据库
        sql = "update server_info set root_password = '%s' WHERE (host_busi_ip = '%s' or host_data_ip = '%s')"
        super(PassWorder,self).update_advanced(sql,encrypt_pass,host_ip,host_ip)

        logger.write_log("%s change password sucess." % host_ip)




