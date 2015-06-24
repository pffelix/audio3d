# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 14:56:04 2015

@author: Marko 
"""

import socket

HOST = 'artrack.clients.ldv.ei.tum.de'
PORT = 50105
UDPPORT = 6666

class DT2(object):
    def __init__(self):
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp.connect((HOST, PORT))

        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.bind(('0.0.0.0', UDPPORT))

        res = self.sendreceive('dtrack2 get system access')
        #if res != 'dtrack2 set system access full':
	#      print("###"+res+"###")
        #    raise Exception()

        self.sendreceive('dtrack2 init')
        self.sendreceive('dtrack2 set output net ch01 udp my_ip %d' % UDPPORT)
        self.sendreceive('dtrack2 tracking start')

    def __del__(self):
        self.sendreceive('dtrack2 tracking stop')
        self.sendreceive('dtrack2 set output net ch01 udp my_ip none')

    def sendreceive(self, cmd):
        self.tcp.send(cmd)
        data = self.tcp.recv(200)
        print(data)
        return data

    def get_measurements(self):
        return self.udp.recvfrom(200)[0]

    def angle(self):
	data = self.get_measurements().split('\n')
	sixds = [ i for i in data if i.startswith('6d ')]
	return sixds

if __name__ == '__main__':
    from time import sleep

    dt2 = DT2()
    while True:
        print(dt2.angle())