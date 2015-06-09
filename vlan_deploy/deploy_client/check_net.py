#!/usr/bin/python
# -*- coding: utf-8 -*-
import netifaces
import argparse,sys
import os, socket, struct, select, time
import re
from IPy import IP
'''
  检查网络以及相关配置
'''

default_timer = time.time

ICMP_ECHO_REQUEST = 8

class MyPing(object):
    def __init__(self):
        pass

    def checksum(self,source_string):
        """
        I'm not too confident that this is right but testing seems
        to suggest that it gives the same answers as in_cksum in ping.c
        """
        sum = 0
        countTo = (len(source_string)/2)*2
        count = 0
        while count<countTo:
            thisVal = ord(source_string[count + 1])*256 + ord(source_string[count])
            sum = sum + thisVal
            sum = sum & 0xffffffff # Necessary?
            count = count + 2

        if countTo<len(source_string):
            sum = sum + ord(source_string[len(source_string) - 1])
            sum = sum & 0xffffffff # Necessary?

        sum = (sum >> 16)  +  (sum & 0xffff)
        sum = sum + (sum >> 16)
        answer = ~sum
        answer = answer & 0xffff

        # Swap bytes. Bugger me if I know why.
        answer = answer >> 8 | (answer << 8 & 0xff00)

        return answer


    def receive_one_ping(self,my_socket, ID, timeout):
        """
        receive the ping from the socket.
        """
        timeLeft = timeout
        while True:
            startedSelect = default_timer()
            whatReady = select.select([my_socket], [], [], timeLeft)
            howLongInSelect = (default_timer() - startedSelect)
            if whatReady[0] == []: # Timeout
                return

            timeReceived = default_timer()
            recPacket, addr = my_socket.recvfrom(1024)
            icmpHeader = recPacket[20:28]
            type, code, checksum, packetID, sequence = struct.unpack(
                "bbHHh", icmpHeader
            )

            if type != 8 and packetID == ID:
                bytesInDouble = struct.calcsize("d")
                timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
                return timeReceived - timeSent

            timeLeft = timeLeft - howLongInSelect
            if timeLeft <= 0:
                return


    def send_one_ping(self,my_socket, dest_addr, ID):
        """
        Send one ping to the given >dest_addr<.
        """
        dest_addr  =  socket.gethostbyname(dest_addr)

        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        my_checksum = 0

        # Make a dummy heder with a 0 checksum.
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytesInDouble = struct.calcsize("d")
        data = (192 - bytesInDouble) * "Q"
        data = struct.pack("d", default_timer()) + data

        # Calculate the checksum on the data and the dummy header.
        my_checksum = self.checksum(header + data)

        # Now that we have the right checksum, we put that in. It's just easier
        # to make up a new header than to stuff it into the dummy.
        header = struct.pack(
            "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
        )
        packet = header + data
        my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1


    def do_one(self,dest_addr, timeout):
        """
        Returns either the delay (in seconds) or none on timeout.
        """
        icmp = socket.getprotobyname("icmp")
        try:
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except socket.error, (errno, msg):
            if errno == 1:
                # Operation not permitted
                msg = msg + (
                    " - Note that ICMP messages can only be sent from processes"
                    " running as root."
                )
                raise socket.error(msg)
            raise # raise the original error

        my_ID = os.getpid() & 0xFFFF

        self.send_one_ping(my_socket, dest_addr, my_ID)
        delay = self.receive_one_ping(my_socket, my_ID, timeout)

        my_socket.close()
        return delay


    def verbose_ping(self,dest_addr, timeout = 1, count = 3):
        """
            检查网络
        """
        for i in xrange(count):
            try:
                delay  =  self.do_one(dest_addr, timeout)
            
            except socket.gaierror, e:
                return False
                break
            except socket.error,e:
                return False
                break

            if delay  ==  None:
                return False
            else:
                delay  =  delay * 1000
                return True


def check_network(ip):
    '''
        检查网络连通性
    '''
    import json
    ip_str = ""
    ip_status = {}

    my_ping = MyPing()
    if my_ping.verbose_ping(ip):
        sys.exit(0)
    else:
        sys.exit(1)
 

def get_main_table():
    '''
       依据 ethX.route 生成对应main路由字典
    '''
    net_dir = "/etc/sysconfig/network-scripts"
    vdevice = ""
    vlan_info_file = "/var/lib/vlan/vlan_stats"
    pattern = re.compile('^v_device_list\:\s(.*)')
    with open(vlan_info_file,'r') as f:
        for line in f.readlines():
            matcher = pattern.match(line.strip("\n"))
            if matcher:
                vdevice += matcher.group(1)
    
    p_addr = re.compile('^ADDRESS[0-9]=(.*)')
    p_net = re.compile('^NETMASK[0-9]=(.*)')
    p_gateway = re.compile('^GATEWAY[0-9]=(.*)')
    route_info = []
    for vdev in vdevice.split():
        route_info_file = os.path.join(net_dir,"%s.route" % vdev)
        with open(route_info_file,'r') as f:
            for line in f.readlines():
                if p_addr.match(line):
                    matcher = p_addr.match(line)
                    ipaddress = matcher.group(1)
                if p_net.match(line):
                    matcher = p_net.match(line)
                    netmask = matcher.group(1)
                    network = IP(ipaddress+"/"+netmask,make_net=True).strNormal(1)
                if p_gateway.match(line):
                    matcher = p_gateway.match(line)
                    gateway = matcher.group(1)
                    route_info.append(network + "via" + gateway + "dev" + vdev)
    
    return route_info


def check_main_table(route_conf_info,route_table_info,count):
    '''
        route_conf_info: 路由配置信息
        conf_conut:      路由配置条目
        route_table_info: 生成的main路由表信息
    '''
    conf_conut = len(route_conf_info)
    if route_table_info == "" or int(count) == 0:
        sys.exit(1)
    
    if int(count) == conf_conut:
        route_info_str = "".join(route_table_info.split())
        if route_info_str in route_conf_info:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(1)



def check_interface(vlan_ip):
    '''
        检查vlan ip是否配置到网卡以及网卡是否激活
    '''
    unuse_dev = []
    up_dev   = {}
    down_dev = {}
    count = 0

    for dev_name in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(dev_name):
            for link in netifaces.ifaddresses(dev_name)[netifaces.AF_INET]:
                    if vlan_ip.strip() == link['addr']:
                        count = count + 1
                    else:
                        pass
    if count != 1:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check network!')
    parser.add_argument('-p', action="store", dest="vlan_ipaddr",help="vlan ip地址")
    parser.add_argument('-n', action="store", dest="ipaddress",help="服务器(包括vlan的)ip地址")
    parser.add_argument('-g', action="store", dest="gateway",help="vlan网关gateway")
    parser.add_argument('-o', action='store', dest="action",help="操作选项")
    parser.add_argument('-c', action='store', dest="route_table_count",help="路由条目")
    parser.add_argument('-s', action='store', dest="route_table_info",help="路由信息")
    results = parser.parse_args()

    if results.action and results.action == "check_interface":
        check_interface(results.vlan_ipaddr)

    if results.action and results.action == "check_network":
        check_network(results.ipaddress)

    if results.action and results.action == "check_route":
        route_conf_info = get_main_table()
        check_main_table(route_conf_info,results.route_table_info,results.route_table_count)

    
