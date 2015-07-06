import socket

HOST = 'artrack.clients.ldv.ei.tum.de'
PORT = 50105
UDPPORT = 6666

# @class <DT2> This class builts up a networking interface using the python
# package socket to extract information gained by an ARTTRACK tracking
# system
# @author Marko Durkovic
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
    
    ## @brief function returns the the received data from the headtracker
    #
    #@author Marko Durkovic
    def get_measurements(self):
        return self.udp.recvfrom(200)[0]

    ## @brief this function reterns the data linewise
    # @details returned data format:
    # ['6d 1 [0 1.000] [x y z polar azimuthal] [3x3 rotation matrix]\r']
    #@author Marko Durkovic
    def angle(self):
        data = self.get_measurements().decode('utf-8')
        data = data.split('\n')
        sixds = [i for i in data if i.startswith('6d ')]
        return sixds


#if __name__ == '__main__':
#    # from time import sleep
#    dt2 = DT2()
#    while True:
#        # print(dt2.angle()[0])
#        # print(type(dt2.angle()))
#        print(azimuth_angle(dt2.angle()[0]))
