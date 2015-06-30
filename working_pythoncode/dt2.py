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
        # res = self.sendreceive('dtrack2 get system access')
        # if res != 'dtrack2 set system access full':
        #    print("###"+res+"###")
        #    raise Exception()
        self.sendreceive('dtrack2 init')
        self.sendreceive('dtrack2 set output net ch01 udp my_ip %d' % UDPPORT)
        self.sendreceive('dtrack2 tracking start')

    def __del__(self):
        self.sendreceive('dtrack2 tracking stop')
        self.sendreceive('dtrack2 set output net ch01 udp my_ip none')

    def sendreceive(self, cmd):
        cmd = cmd.encode('utf-8')
        self.tcp.send(cmd)
        data = self.tcp.recv(200)
        print(data)
        return data

    def get_measurements(self):
        return self.udp.recvfrom(200)[0]

    def angle(self):
        data = self.get_measurements().decode('utf-8')
        data = data.split('\n')
        sixds = [i for i in data if i.startswith('6d ')]
        return sixds

    # -*- coding: utf-8 -*-
    """
    Created on Tue Jun 23 16:46:54 2015

    @author: mh
    """
# import math


def clean_and_split(line):
    stripped = str(line)
    unquoted = stripped.replace("]", "")   # remove " occurrences in string
    clean = unquoted.split("[")          # split at first ,
    return clean


def string_to_float(s):
    angle_float = []
    stripped = s.strip()
    split = stripped.split(" ")
    for i in split:
        angle = float(i)
        angle_float.append(angle)
    return angle_float


def azimuth_angle(data):
    data_format = clean_and_split(data)
    angle = '0'
    try:
        angle = data_format[2]
    except IndexError:
        pass
    angle_list = map(float, angle)
    #angle_list = string_to_float(angle)
    azimuth = 0
    try: 
        azimuth = angle_list[5]
    except IndexError:
        pass
    if azimuth <= 0:
        azimuth = -1*azimuth
    else:
        azimuth = 360 - azimuth
    return azimuth


if __name__ == '__main__':
    # from time import sleep
    dt2 = DT2()
    while True:
        # print(dt2.angle()[0])
        # print(type(dt2.angle()))
        print(azimuth_angle(dt2.angle()[0]))
