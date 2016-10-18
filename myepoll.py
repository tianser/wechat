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
import Queue
import common

class Epoll(object):
    def __init__(self):
        self.fileno_to_connection = {}
        self.fileno_to_ip = {}
        self.send_msg = {}
        try:
            self.listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        except socket.error, msg:
            Log.error("create socket failed")
            sys.exit(0)

        try:
            self.listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error, msg:
            Log.error("setsocketopt SO_REUSEADDR failed")
            sys.exit(0)

        try:
            self.listen_fd.bind(('0.0.0.0',9999))
        except socket.error, msg:
            Log.error("bind failed")
            sys.exit(0)

        try:
            self.listen_fd.listen(10)
        except socket.error, msg:
            Log.error(msg)
            sys.exit(0)
        
        try:
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(self.listen_fd.fileno(), select.EPOLLIN)
        except select.error, msg:
            Log.error(msg)
            sys.exit(0)

    def Modify(self):
        while True:
            if not send.empty():
                msg = send.get().split(":")
                print "whileName:", g_val.whiteName.keys()
                if msg[0] in g_val.whiteName.keys():
                    Log.info("send: %s" % msg[1])
                    print "fileno_to_ip:", self.fileno_to_ip
                    for fileno, ipaddr in self.fileno_to_ip.items():
                        if ipaddr == g_val.whiteName[ msg[0] ]:
                           Log.info("modify %d", fileno) 
                           #self.epoll_fd.modify(fileno, select.EPOLLET | select.EPOLLOUT)
                           self.send_msg[fileno] = msg[1]
            else:
                break

    def hanle_event(self):
        #datalist = {}
        while True:
            Log.debug("Modify start")
            Epoll.Modify(self)	
            Log.debug("Modify end")
            epoll_list = self.epoll_fd.poll()
            for fd, events in epoll_list:
                Log.debug("list epoll ")
                if fd == self.listen_fd.fileno():
                    conn, addr = self.listen_fd.accept()
                    Log.debug("accept connection from %s, %d, fd = %d" % (addr[0], addr[1], conn.fileno()))
                    conn.setblocking(0)
                    self.epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                    self.fileno_to_connection[conn.fileno()] = conn
                    self.fileno_to_ip[conn.fileno()] = addr[0]
                elif select.EPOLLIN & events:
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
                        except socket.error, msg:
                            if msg.errno == errno.EAGAIN:
                                Log.debug("%s receive %s" % (fd, datas))
                                self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                                recv.put(datas)
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
                    Log.debug("out info %d" %fd)
                    if fd in self.send_msg.keys():
                        Log.info("send msg , %s" % self.send_msg[fd])
                        #self.fileno_to_connection[fd].send(self.send_msg[fd], len(self.send_msg[fd]))
                        self.fileno_to_connection[fd].sendall(self.send_msg[fd])
                        del self.send_msg[fd]
                        Log.info("send msg ok")
                    self.epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)
                    break 
                else:
                    break 
def process1():
    ep = Epoll()
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

def process2():
    now = time.time()
    while True:
        Log.info("process2.....")
        if time.time() - now > 30:
            Log.info("process2  send 发送: TT" )
            now = time.time()
            send.put("1:ceph -s")
            while True:
                if not recv.empty():
                    Log.info("recv收到 :%s" %recv.get())
                else:
                    Log.info("recv empty")
                    break
        else :
            time.sleep(3)

if __name__ == "__main__":
    g_val = common.Global()
    g_val.GetWhiteName()
    recv = multiprocessing.Queue()
    send = multiprocessing.Queue()
    pw = multiprocessing.Process(target=process1)
    pr = multiprocessing.Process(target=process2)
    pw.start()
    pr.start()
    pw.join()
    pr.join()
