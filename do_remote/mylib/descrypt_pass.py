import base64
import hashlib
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

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def decrypt_pass(self,source_filename):
        with open(source_filename,'r') as f:
            for line in f.readlines():
                host_ip = line.split(",")[1]
                enc_pass = line.split(",")[0]
                raw_pass = self.decrypt(enc_pass)
                print host_ip,raw_pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Init machine')
    parser.add_argument('-s', action="store", dest="action",help="解密")
    parser.add_argument('-f', action="store", dest="filename",help="-f 指定配置文件,默认/tmp/machine.list.pass")

    results = parser.parse_args()

    if not results.filename:
        source_filename = "/tmp/machine.list.pass"
    else:
        source_filename = results.filename

    if results.action == "init":
        main("init",source_filename)
    else:
        parser.print_help()
