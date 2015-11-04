export PATH=/usr/lib64/qt-3.3/bin:/usr/local/sbin:/usr/sbin:/sbin:/usr/local/bin:/bin:/usr/bin:/root/bin
WEB_DIR="/data/sys_resource_repo/sec/init_web"
DB_DIR="/data/sys_resource_repo/sec/init_db"

BIZOP_KEY="from=\"10.11.199.180,10.13.199.180\",no-agent-forwarding,no-port-forwarding ssh-dss AAAAB3NzaC1kc3MAAACBAO+yhNAkOZbhvK+CTx1zn6C0CfabaoAZLd2P4OZBi1GR+5S3HUnn9DkfMFXWfvrTBgyUJYWzg76Ymp4hlsZFLV/TR0yhPdIPWYSqAXgerzhx8u3TxxPVpgXzGlXSV424a+6n5XzeQFfj59DvKV4Y1KZqIQNngVkxtDecq2j4SfVfAAAAFQD5YJHwbyzzoV1TUNkNSvZo81ZQ8QAAAIEA19htkFN3vxdrEF571Jt0ACxFBx4xwsrrcbsyrPvJdqxhM85X6EREepIAGs5ronv2y//09WDs/APpoGU/jHwEdhBqXDUJehRzqEbLuY44hLk/DqWiXcrS4mkILqEWqsd5KDG6P1YwG5ezRslf9mrfi9zkGpPmNNATbkB7IMiCvDYAAACBAJcDObyRlj11hBvykYvdA3MU5ywRI8I8w+ldLSoYD3gZ7jVM+dF7H1x5uJFdbi2rXbceJfwABBVQwCh/yamgh+QfjgMoFeJ3/famFd8kqNsw8Y34s4eAVUVv/Xus6KX3OTIiqJjeD1T3pxYKCRLfuATuDSGQAmNhfMikj68w/JGz root@tc_202_117"

OP_KEY="from=\"10.147.239.235,10.137.239.235,10.146.239.235,10.136.239.235,10.147.239.1,10.137.239.1,10.146.239.1,10.136.239.1\",no-agent-forwarding,no-port-forwarding ssh-dss AAAAB3NzaC1kc3MAAACBAPx3767ksyO+E+L6fmIKJ+2Uq6yyyk3F83DQ2J+BLZgkzJG6K9FaoFLJQa+iLu3eL9ik+8/oNYcv96dL4M7tZRrQy0swBzIRlEhVRSMN7Ptiu+2TfNfgujA4PVPIvjPqVcbal1frEIy7VHQHSuVMwMI/6edd6J9FAo9CPHnsIlSdAAAAFQCFzOzFUZyUP9cOD+ubopSb+j3z0wAAAIBYXQOIRHmxk0hlwh13seetRtrkNYp1QGkaSLu8KvSr3cmGAUSndqxPVgvL5xT/C3S+sABB4H5KGpxlqTmqNn2MWM+oX4HBmsKXzslxIp0tlwqUE4DWaNvCEiKBqEBnWM+QTlSZ5C0kTJl+Os4rfEYC46R0bhHhYxc6NnpNyYv6JwAAAIBktn02O6k+Tg6CwN1RcG+RMZcqwZaUJ/kgDha3Ho9CZCcC5mNiC36M1qGW0J47RoEe5vSAsTitBgyr3pPEZp5+pnJjaXVo3uRWVtsAodDoWG0dOqYEIeX03VqrFQrt3SBsezPrpKoxZgItSbR6XnkK42iSrgk/f6Eyd3ckbh5a7Q== root@tc_239_235"


echo "$BIZOP_KEY" > $WEB_DIR/authorized_keys
echo "$OP_KEY" >> $WEB_DIR/authorized_keys
echo "$OP_KEY" > $DB_DIR/authorized_keys

chmod 644 $WEB_DIR/authorized_keys
chmod 644 $DB_DIR/authorized_keys

