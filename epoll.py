#!/usr/bin/python
#encoding=utf-8

import socket
import thread
import select, errno
import sys
from common import Log as Log
from multiprocessing import Process,Queue,Pool, Manager, Value, Array
import pdb 
import multiprocessing
import time
import Queue
import common
import threading
import signal

class Heart(object):
    def __init__(self):
        self.start = int(time.time())
        self.count = 0
   
    def reset(self):
        self.count = 0

    def HeartHandle(self):
        while True: 
            now = int(time.time())
            if now - self.start > 10:
                self.start = now 
                self.count = self.count + 1
            else:
                time.sleep(3)

class Epoll(object):
    def __init__(self):
        self.fileno_to_connection = {}
        self.fileno_to_ip = {}
        self.send_msg = {}
        self.heart    = {}
        self.lock  = threading.Lock()
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
            self.epoll_fd.register(self.listen_fd.fileno(), select.EPOLLIN |select.EPOLLOUT)
        except select.error, msg:
            Log.error(msg)
            sys.exit(0)

    def Modify(self, send, g_val):
        while True:
            if g_val.ExitFlag.value == 1:
                thread.exit_thread()
            for key, value in self.heart.items():
                if value.count > 5:
                    self.epoll_fd.modify(key, select.EPOLLHUP)
            lst = []
            if not send.empty():
                self.lock.acquire()
                msg = send.get().split(":")
                Log.info("msg :%s"% msg)
                Log.info("fileno_to_ip:%s"% self.fileno_to_ip)
                Log.info("white_Name %s " % g_val.whiteName)
                if msg[0] in g_val.whiteName.keys():
                    for fileno, ipaddr in self.fileno_to_ip.items():
                        if ipaddr == g_val.whiteName[ msg[0] ]:
                           self.epoll_fd.modify(fileno, select.EPOLLIN | select.EPOLLOUT)
                           Log.info("filno: %d send msg: %s" %(fileno, msg[1] ))
                           lst.append(msg[1]) 
                           if len(lst) > 0: 
                               self.send_msg[fileno] = lst 
                Log.info("self.send_msg===:%s" % self.send_msg)
                self.lock.release()
            else:
                time.sleep(1) 
    
    def HeartBeat(self, g_val):
       run_list = []
       while True:
           if g_val.ExitFlag.value == 1:
               thread.exit_thread()
           for id in run_list:
              if id not in self.heart.key():
                  run_list.remove(id)
           for key, value in self.heart.items():
               if key not in run_list:
                   run_list.append(key)
                   value.HeartHandle()
           time.sleep(1) 

    def hanle_event(self, send, recv, g_val):
        #datalist = {}
        HB = thread.start_new_thread(Epoll.HeartBeat, (self, g_val )) 
        Modify = thread.start_new_thread(Epoll.Modify, (self, send, g_val)) 
        while True:
            if g_val.ExitFlag.value == 1:
                break
            epoll_list = self.epoll_fd.poll()
            for fd, events in epoll_list:
                if fd == self.listen_fd.fileno():
                    conn, addr = self.listen_fd.accept()
                    Log.debug("accept connection from %s, %d, fd = %d" % (addr[0], addr[1], conn.fileno()))
                    if addr[0] not in g_val.whiteName.values():
                        Log.error("unkown connections frome %s, close it" % addr[0])
                        conn.close() 
                        break
                    conn.setblocking(0)
                    self.epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                    self.fileno_to_connection[conn.fileno()] = conn
                    self.heart[conn.fileno()] = Heart() 
                    self.fileno_to_ip[conn.fileno()] = addr[0]
                elif select.EPOLLIN & events:
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
                                Log.debug("%s receive %s" % (fd, datas))
                                #self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                                self.heart[fd].reset()
                                if datas != "heart beat":
                                    for region, ipaddr  in g_val.whiteName.items():
                                        if ipaddr == self.fileno_to_ip[fd]:
                                            recv.put("[ " + region+ " ]:#"+datas)
                                            break
                                else:
                                    self.fileno_to_connection[fd].sendall("server|heart echo")
                                    #self.send_msg[fd] = ["server|heart echo"] 
                                    #self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                                    
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
                    del self.fileno_to_connection[fd]
                    del self.heart[fd]
                    del self.fileno_to_ip[fd]
                    break 
                elif select.EPOLLOUT & events:
                    Log.debug("epoll out %d" %fd)
                    self.lock.acquire()
                    Log.debug("send_msg--===-:%s" % self.send_msg )
                    if fd in self.send_msg.keys():
                        for msg in self.send_msg[fd]:
                            Log.info("send msg:%s" % msg)
                            #self.fileno_to_connection[fd].send(self.send_msg[fd], len(self.send_msg[fd]))
                            self.fileno_to_connection[fd].sendall(msg)
                        del self.send_msg[fd]
                        Log.info("send msg ok")
                    else:
                        Log.info("send  msg empty")
                    self.lock.release()
                    self.epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)
                    break 
                else:
                    break 

def EpollServer(send, recv, g_val):
    ep = Epoll()
    ep.hanle_event(send, recv, g_val)
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
        if time.time() - now > 30:
            Log.info("process2  send 发送: TT" )
            now = time.time()
            send.put("1:ggg|ceph -s")
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
