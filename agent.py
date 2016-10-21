#!/usr/bin/python
#encoding=utf-8

import thread
import socket
import select, errno
import sys
from common import Log as Log
from multiprocessing import Process,Queue,Pool, Manager, Value, Array
import pdb 
import multiprocessing
import time
import common
import Queue
import weixin

class Epoll(object):
    def __init__(self):
        self.fileno_to_connection = {}
        self.send_msg = {}
        try:
            self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        except socket.error, msg:
            Log.error("create socket failed")
            sys.exit(0)

        try:
            self.fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error, msg:
            Log.error("setsocketopt SO_REUSEADDR failed")
            sys.exit(0)

        try:
            self.fd.bind(('127.0.0.1',9997))
        except socket.error, msg:
            Log.error("bind failed")
            sys.exit(0)

        try:
            self.fd.connect(('192.168.39.172',9999))
            self.fd.setblocking(0)
            self.fileno_to_connection[self.fd.fileno()] = self.fd
        except socket.error, msg:
            Log.error("connect failed")
            sys.exit(0)
        
        try:
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(self.fd.fileno(), select.EPOLLIN)
        except select.error, msg:
            Log.error(msg)
            sys.exit(0)

    def Modify(self):
        while True:
            if not send.empty():
                self.epoll_fd.modify(self.fd.fileno(), select.EPOLLET | select.EPOLLOUT)
            else:
                time.sleep(1) 

    def hanle_event(self):
        thread.start_new_thread(Epoll.Modify, (self, ))
        while True:
            epoll_list = self.epoll_fd.poll()
            for fd, events in epoll_list:
                if select.EPOLLIN & events:
                    datas = ''
                    while True:
                        try:
                            data = self.fileno_to_connection[fd].recv(10)
                            if not data and not datas:
                                self.epoll_fd.unregister(fd)
                                self.fileno_to_connection[fd].close()
                                Log.debug("%s closed" % self.fileno_to_ip[fd])
                                break
                            else:
                                datas += data
                        except socket.error, msg:
                            if msg.errno == errno.EAGAIN:
                                Log.debug("%s receive %s" % (fd, datas)) #  ggg:ceph -s
                                recv_msg = datas.split("|")
                                status, output = common.sh_cmd(recv_msg[1])
                                send.put(recv_msg[0]+ "@" + output)
                                self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                                break
                            else:
                                self.epoll_fd.unregister(fd)
                                self.fileno_to_connection[fd].close()
                                Log.error(msg)
                                break
                    break 
                elif select.EPOLLHUP & events:
                    self.epoll_fd.unregister(fd)
                    self.fileno_to_connection[fd].close()
                    Log.debug("%s closed" % self.fileno_to_ip[fd])
                    break 
                elif select.EPOLLOUT & events:
                    while True:
                        if not send.empty():
                            self.fileno_to_connection[fd].sendall(send.get())
                        else:
                            break 
							
                    self.epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)
                    break 
                else:
                    break 
def process1():
    ep = Epoll()
    ep.hanle_event()

def notifyMode():
    Log.debug("enter notify success")
    now = int(time.time())
    while True:
        if int(time.time()) - now > 300 and g_val.autonotify.value:  
            now = int(time.time())
            status, output = common.sh_cmd("ceph health detail")    
            if output != "HEALTH_OK":
                status, msg = common.sh_cmd("ceph -s")   
                send.put(msg)
        else:
            time.sleep(5)	#(60)

if __name__ == "__main__":
    g_val = common.Global()
    g_val.ParserArg()
    recv = multiprocessing.Queue()
    send = multiprocessing.Queue()
    pw = multiprocessing.Process(target=process1)
    pr = multiprocessing.Process(target=notifyMode)
    pw.start()
    pr.start()
    pw.join()
    pr.join()
