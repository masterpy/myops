from Crypto.Cipher import AES
from Crypto import Random
import pprint

BS = 32
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(s[-1])]
 


class AESCipher:
    def __init__( self, key ):
        """
        Requires hex encoded param as a key
        """
        self.key = key.decode("hex")
 
    def encrypt( self, raw ):
        """
        Returns hex encoded encrypted value!
        """
        raw = pad(raw)
        iv = Random.new().read(AES.block_size);
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        #pprint.pprint(iv + cipher.encrypt( raw ))
        #
        return ( iv + cipher.encrypt( raw ) ).encode("hex")
 
    def decrypt( self, enc ):

        """
        Requires hex encoded param to decrypt
        """
        enc = enc.decode("hex")         
        iv = enc[:16]
        enc= enc[16:]

        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        pprint.pprint(cipher.decrypt( enc))
        return unpad(cipher.decrypt( enc))
 
if __name__== "__main__":
    key = "CpVw7ChmK2ZQwgTejpf2oAdiKzH8D8AC".encode("hex")
    key=key[:32]
    decryptor = AESCipher(key)
    plaintext = decryptor.encrypt("abc")

    #plaintext = decryptor.decrypt(ciphertext)
    print "%s" % plaintext