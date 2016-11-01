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
import json
reload(sys)
sys.setdefaultencoding('utf8')

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

class Epoll(common.SigHandle):
    def __init__(self):
        super(Epoll, self).__init__()
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

    def Modify(self, send, recv, g_val):
        while True:
            if self.Flag:
                thread.exit_thread()
            for fd, value in self.heart.items():
                if value.count > 5:
                    self.epoll_fd.unregister(fd)
                    self.fileno_to_connection[fd].close()
                    Log.error("heart_beat: %s lost, close it" % self.fileno_to_ip[fd])
                    for region, ip in g_val.whiteName.items(): 
                        if ip == self.fileno_to_ip[fd] :
                            recv.put(common.encodeMsg("@@@@", "heart beat lost", region))
                            break
                    del self.fileno_to_connection[fd]
                    del self.heart[fd]
                    del self.fileno_to_ip[fd]
                    #self.epoll_fd.modify(key, select.EPOLLHUP)
            lst = []
            while True:
                if not send.empty():
                    self.lock.acquire()
                    try:
                        msg = json.loads(send.get())
                    except  Exception as e:
                        Log.error("json parse error, %s" % str(e))
                        self.lock.release()
                        continue
                    if msg["content"] == "Online":
                        rt = ""
                        for region, ipaddr in g_val.whiteName.items():
                            if ipaddr in self.fileno_to_ip.values():
                                rt = rt + region +" "  
                        if not rt:
                            rt = "no region"
                        recv.put(common.encodeMsg(msg["fromTo"], rt + " online now", msg["sendTo"]))
                        self.lock.release()
                        continue
                    if msg["sendTo"] in g_val.whiteName.keys():
                        for fileno, ipaddr in self.fileno_to_ip.items():
                            if ipaddr == g_val.whiteName[ msg["sendTo"] ]:
                               self.epoll_fd.modify(fileno, select.EPOLLIN | select.EPOLLOUT)
                               Log.info("filno: %d send msg: %s"%(fileno, msg["content"]))
                               if fileno in self.send_msg.keys():
                                   self.send_msg[fileno].append( common.encodeMsg(msg["fromTo"], msg["content"], msg["sendTo"]) )
                               else:
                                   lst.append( common.encodeMsg(msg["fromTo"], msg["content"], msg["sendTo"]) )
                                   self.send_msg[fileno] = lst 
                    self.lock.release()
                else:
                    time.sleep(1) 
                    break
    
    def HeartBeat(self, g_val):
       run_list = []
       while True:
           if self.Flag:
               thread.exit_thread()
           for id in run_list:
              if id not in self.heart.key():
                  run_list.remove(id)
           for key, value in self.heart.items():
               if key not in run_list:
                   run_list.append(key)
                   value.HeartHandle()
           time.sleep(1) 

    def Xhandler(self, signum, frame):
        common.SigHandle.handler(self, signum, frame)
        while True:
            if self.Flag == 2:
                for fd, conn  in self.fileno_to_connection.items():
                    self.epoll_fd.unregister(fd)
                    self.fileno_to_connection[fd].close()
                    Log.debug("%s closed" % self.fileno_to_ip[fd])
                    del self.fileno_to_connection[fd]
                    del self.heart[fd]
                    del self.fileno_to_ip[fd]
            else:
                time.sleep(1)

    def hanle_event(self, send, recv, g_val):
        #datalist = {}
        HB = thread.start_new_thread(Epoll.HeartBeat, (self, g_val )) 
        Modify = thread.start_new_thread(Epoll.Modify, (self, send, recv, g_val)) 
        while True:
            if self.Flag:
                Log.info("handle_event exit.....")
                for fd, conn  in self.fileno_to_connection.items():
                    self.epoll_fd.unregister(fd)
                    self.fileno_to_connection[fd].close()
                    Log.debug("%s ===closed" % self.fileno_to_ip[fd])
                    del self.fileno_to_connection[fd]
                    del self.heart[fd]
                    del self.fileno_to_ip[fd]
                break
            try:
                epoll_list = self.epoll_fd.poll()
            except IOError:
                continue
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
                                try:
                                    msg = json.loads(datas)
                                    if msg["content"] == "heart beat":
                                        self.fileno_to_connection[fd].sendall( common.encodeMsg(msg["sendTo"], "heart echo", msg["fromTo"]) )
                                        break
                                    if msg["sendTo"] == "all":
                                        for region, ipaddr in g_val.whiteName.items():
                                            if ipaddr == self.fileno_to_ip[fd]:
                                                msg["sendTo"] = region
                                                break
                                        datas = common.encodeMsg(msg["fromTo"], msg["content"], msg["sendTo"])
                                    recv.put( datas )
                                except Exception as e:
                                    Log.error("load parse error, %s" % e)
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
                    self.lock.acquire()
                    if fd in self.send_msg.keys():
                        for msg in self.send_msg[fd]:
                            Log.info("fileno %d, send:%s" %(fd, msg) )
                            #self.fileno_to_connection[fd].send(self.send_msg[fd], len(self.send_msg[fd]))
                            self.fileno_to_connection[fd].sendall(msg)
                        del self.send_msg[fd]
                    else:
                        Log.error("send msg empty")
                    self.lock.release()
                    self.epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)
                    break 
                else:
                    break 

def EpollServer(send, recv, g_val):
    ep = Epoll()
    ep.hanle_event(send, recv, g_val)
