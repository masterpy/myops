#!/usr/bin/python
import sys


def ssh_update_key(file):
    with open(file,'r') as f:
        for line in f.readlines():
            host = line.split()[0]
            user = 'root'
            password = "noSafeNoWork@2014"
            port = 22
            key = "ssh-dss AAAAB3NzaC1kc3MAAACBAO+yhNAkOZbhvK+CTx1zn6C0CfabaoAZLd2P4OZBi1GR+5S3HUnn9DkfMFXWfvrTBgyUJYWzg76Ymp4hlsZFLV/TR0yhPdIPWYSqAXgerzhx8u3TxxPVpgXzGlXSV424a+6n5XzeQFfj59DvKV4Y1KZqIQNngVkxtDecq2j4SfVfAAAAFQD5YJHwbyzzoV1TUNkNSvZo81ZQ8QAAAIEA19htkFN3vxdrEF571Jt0ACxFBx4xwsrrcbsyrPvJdqxhM85X6EREepIAGs5ronv2y//09WDs/APpoGU/jHwEdhBqXDUJehRzqEbLuY44hLk/DqWiXcrS4mkILqEWqsd5KDG6P1YwG5ezRslf9mrfi9zkGpPmNNATbkB7IMiCvDYAAACBAJcDObyRlj11hBvykYvdA3MU5ywRI8I8w+ldLSoYD3gZ7jVM+dF7H1x5uJFdbi2rXbceJfwABBVQwCh/yamgh+QfjgMoFeJ3/famFd8kqNsw8Y34s4eAVUVv/Xus6KX3OTIiqJjeD1T3pxYKCRLfuATuDSGQAmNhfMikj68w/JGz root@tc_202_117"
            command = "mkdir -p ~/.ssh && echo %s > ~/.ssh/authorized_keys" % key
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(host,port,user,password)
            stdin,stdout,stderr = c.exec_command(command)
            c.close()
            check_update_key(host)

def check_update_key(remote_ip):
    host = "10.13.199.180"
    user = "root"
    port = 22
    passwd = "8d3Tq#:B"

    command = "str=$(ssh %s \"ifconfig $1|sed -n 2p\") && echo $str | awk '{print $2}'"  % remote_ip

    c = paramiko.SSHClient()
    c.load_system_host_keys()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host,port,user,passwd)
    stdin,stdout,stderr = c.exec_command(command)
    print stdout.read()
    c.close()

if __name__ == "__main__":
  if len(sys.argv) < 2:
         print 'No action specified.'
         sys.exit(1)
  file_name = sys.argv[1]
  ssh_update_key(file_name)
