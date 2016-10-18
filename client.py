#!/usr/bin/python
#encoding=utf-8

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
            self.fd.bind(('0.0.0.0',9998))
        except socket.error, msg:
            Log.error("bind failed")
            sys.exit(0)

        try:
            self.fd.connect(('127.0.0.1',9999))
            self.fd.setblocking(0)
            self.fileno_to_connection[self.fd.fileno()] = self.fd
        except socket.error, msg:
            Log.error("connect failed")
            sys.exit(0)
        
        Log.info("connect ok") 
        try:
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(self.fd.fileno(), select.EPOLLOUT)
        except select.error, msg:
            Log.error(msg)
            sys.exit(0)

    def Modify(self):
        while True:
            if not send.empty():
                #msg = send.get()
                self.epoll_fd.modify(self.fd.fileno(), select.EPOLLET | select.EPOLLOUT)
                Log.info("modify ok")
                break
            else:
                break

    def hanle_event(self):
        epoll_list = self.epoll_fd.poll()
        while True:
            Log.info("check fd") 
            time.sleep(2) 
            Epoll.Modify(self)
            Log.info("check fd end") 
            for fd, events in epoll_list:
                Log.debug("list epoll ")
                if select.EPOLLIN & events:
                    Log.debug("fd in")
                    datas = ''
                    while True:
                        try:
                            data = self.fileno_to_connection[fd].recv(10)
                            Log.debug("part of msg: %s" % data) 
                            if not data and not datas:
                                self.epoll_fd.unregister(fd)
                                self.fileno_to_connection[fd].close()
                                Log.debug("%s closed" % self.fileno_to_ip[fd])
                                break
                            else:
                                datas += data
                                break 
                        except socket.error, msg:
                            if msg.errno == errno.EAGAIN:
                                Log.debug("%s receive %s" % (fd, datas)) #  ggg:ceph -s
                                recv_msg = datas.split(":")
                                status, output = common.sh_cmd(recv_msg[1])
                                send.put(recv_msg[0] + "|" + output)
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
                    Log.info("send msg start")
                    while True:
                        if not send.empty():
                            self.fileno_to_connection[fd].sendall(send.get())
                            Log.info("send msg ok")
                        else:
                            Log.info("send queue is empty")
                            break
                    self.epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)
                    break 
                else:
                    break 
def process1():
    ep = Epoll()
    Log.info("hanle_event")
    ep.hanle_event()
"""
    now = time.time()
    while True:
        Log.info("process1.....")
        if time.time() - now >2:
            now = time.time()
            Log.info("process1 recv 发送 : 上海 " )
            recv.put("上海:shanghai")
            while True:
                if not send.empty():
                    Log.info("send 收到: %s" % send.get())
                else:
                    Log.info("send empty")
                    break
        else:
            time.sleep(1)
"""

def notifyMode():
    Log.debug("enter notifyMode")
    now = int(time.time())
    while True:
        if int(time.time()) - now > 30 and g_val.autonotify.value:  
            now = int(time.time())
            Log.debug("once again") 
            status, output = common.sh_cmd("ceph health detail")    
            if output != "HEALTH_OK":
                status, output = common.sh_cmd("ceph -s")   
                if g_val.updateconfig:
                    g_val.ParserArg()
                for name in g_val.member:
                    msg = name + "|" + "Wechat自动报警:\n" + output 
                    send.put(msg)
                    Log.debug("send put msg ok") 
        else:
            time.sleep(5)	#(60)

if __name__ == "__main__":
    g_val = weixin.Global()
    g_val.ParserArg()
    recv = multiprocessing.Queue()
    send = multiprocessing.Queue()
    pw = multiprocessing.Process(target=process1)
    pr = multiprocessing.Process(target=notifyMode)
    pw.start()
    pr.start()
    pw.join()
    pr.join()
