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
import json
import Queue
import signal
reload(sys)
sys.setdefaultencoding('utf8')

class Heart(object):
    """Heart beat mechanism wrapper, 30seconds"""
    def __init__(self):
        """Initialize instance
		:params start: create instance time 
		:params count: Heart beat counter
		:returns None
		"""
        self.start = int(time.time())
        self.count = 0

    def reset(self):
        """reset Heart beat counter"""
        self.count = 0

    def HeartHandle(self):
        """Heart beat count"""
        while True:
            now = int(time.time())
            if now - self.start > 10:
                self.start = now
                self.count = self.count + 1
            else:
				time.sleep(3)

class Epoll(object):
    """ net Events handler wrapper"""
    def __init__(self):
        """Initialize
		:params fileno_to_connection: fd and connection 
		:params heart: heart beat instance 
		:params send_msg: msg want to send
		:returns: None
		"""
        self.fileno_to_connection = {}
        self.heart = {}
        self.send_msg = {}

    def bind_and_connect(self):
        """ bind and connect wechat Server
		:raise Exception and exit
		"""
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
            self.fd.bind((g_val.Ip, int(g_val.MyPort)))
        except socket.error, msg:
            Log.error("bind:%s failed" % g_val.MyPort)
            sys.exit(0)          

        try:
            self.fd.connect((g_val.ServerIp,9999))
            self.fd.setblocking(0)
            self.fileno_to_connection[self.fd.fileno()] = self.fd
            self.heart[self.fd.fileno()] = Heart()
        except socket.error, msg:
            Log.error("connect %s:9999 failed" % g_val.ServerIp)
            sys.exit(0)          
        
        try:
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(self.fd.fileno(), select.EPOLLIN)
        except select.error, msg:
            Log.error(msg)
            sys.exit(0)          
       
    def reconnect(self):
        """reconnect wechat server when disconnection"""
		g_val.NotifyFlag.value = 0		#此时无法连接到server端，定时任务关闭
        try:
            self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        except socket.error, msg:
            Log.error("create socket failed")
            return           

        try:
            self.fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error, msg:
            Log.error("setsocketopt SO_REUSEADDR failed")
            return           

        try:
            self.fd.bind((g_val.Ip, int(g_val.MyPort)))
        except socket.error, msg:
            Log.error("bind:%s failed" % g_val.MyPort)
            return           
               
        try:
            self.fd.connect((g_val.ServerIp,9999))
            self.fd.setblocking(0)
            self.fileno_to_connection[self.fd.fileno()] = self.fd
            self.heart[self.fd.fileno()] = Heart()
        except socket.error, msg:
            Log.error("connect %s:9999 failed, %s" % (g_val.ServerIp, msg) )
            return          
        
        try:
            self.epoll_fd = select.epoll()
            self.epoll_fd.register(self.fd.fileno(), select.EPOLLIN)
        except select.error, msg:
            Log.error(msg)
            return          
		g_val.NotifyFlag.value = 1		#此时连接到server端，定时任务重新开启

    def Modify(self):
        while True:
            for fd, value in self.heart.items():
                if value.count > 5:
                    self.epoll_fd.unregister(fd)
                    self.fileno_to_connection[fd].close()
                    del self.fileno_to_connection[fd]
                    del self.heart[fd]
                    #self.epoll_fd.modify(key, select.EPOLLET | select.EPOLLHUP)
            if not send.empty() and self.fileno_to_connection:
                self.epoll_fd.modify(self.fd.fileno(), select.EPOLLET | select.EPOLLOUT)
            else:
                time.sleep(1)

    def HeartBeat(self):
       run_list = []
       while True:
           for id in run_list:
              if id not in self.heart.key():
                  run_list.remove(id)
           for key, value in self.heart.items():
               if key not in run_list:
                   run_list.append(key)
                   value.HeartHandle()
               if value.count > 5:
                   self.epoll_fd.unregister(key)
                   self.fileno_to_connection[key].close()
                   del self.fileno_to_connection[key]
                   del self.heart[key] 
           time.sleep(1)

    def hanle_event(self):
        Log.info("wait msg")
        thread.start_new_thread(Epoll.Modify, (self, ))
        thread.start_new_thread(Epoll.HeartBeat, (self, ))
        while True:
            if g_val.ExitFlag.value == 1:
                Log.info("HandleMsg exit") 
                sys.exit(0)
            #print self.fileno_to_connection
            #if not send.empty() and self.fileno_to_connection:
            #    Log.info("send not empty")
            #    if self.fileno_to_connection:
            #        self.epoll_fd.modify(self.fd.fileno(), select.EPOLLET | select.EPOLLOUT)
            if not self.fileno_to_connection:
                self.reconnect()
            if not self.fileno_to_connection:
                time.sleep(3)
                continue
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
                                del self.fileno_to_connection[fd]
                                del self.heart[fd] 
                                break
                            else:
                                #Log.info("recv data:", data)
                                datas += data
                        except socket.error, msg:
                            if msg.errno == errno.EAGAIN:
                                Log.debug("fd:%s receive %s" % (fd, datas)) #  ggg:ceph -s
                                self.heart[fd].reset()
                                msg = None 
                                try:
                                    msg = json.loads(datas)
                                except Exception as e:
                                    Log.error("json parse Error, datas:%s, error: %s" %(datas, str(e) ) )
                                if not msg:
                                    break
                                if msg["content"] == "Notify":
                                    if g_val.NotifyFlag.value == 0:
                                        g_val.NotifyFlag.value = 1 
                                    else:
                                        g_val.NotifyFlag.value = 0
                                    output = "Nofify Mode set success"
                                elif msg["content"] == "heart echo":
                                    Log.info("recv heart echo from server")
                                    break
                                else:
                                    status, output = common.sh_cmd(msg["content"])
                                if output != "":
                                    #msg["fromTo"]: 昵称， msg["sendTo"]: region
                                    send.put( common.encodeMsg(msg["fromTo"], output, msg["sendTo"]) )
                                    Log.info("====cmd: %s output: %s" % (msg["content"] ,output) )
                                    self.epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                                break
                            else:
                                self.epoll_fd.unregister(fd)
                                self.fileno_to_connection[fd].close()
                                del self.fileno_to_connection[fd]
                                del self.heart[fd]
                                Log.error(msg)
                                break
                    break 
                elif select.EPOLLHUP & events:
                    self.epoll_fd.unregister(fd)
                    self.fileno_to_connection[fd].close()
                    del self.fileno_to_connection[fd]
                    del self.heart[fd] 
                elif select.EPOLLOUT & events:
                    while True:
                        if not send.empty():
                            self.fileno_to_connection[fd].sendall(send.get())
                        else:
                            break 
                    self.epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)
                    break 
                else:
                    time.sleep(1)
                    break

def handle(signum, stack_frame):
    if g_val.NotifyFlag.value:
        status, output = common.sh_cmd("ceph health detail")
        Log.info(":%s" % output)
        if output != "HEALTH_OK":
            status, msg = common.sh_cmd("ceph -s")
            Log.info("msg %s" % msg)
            send.put( common.encodeMsg("@@@@", msg, "all") )
    signal.alarm(300)

def NotifyMode():
    Log.debug("enter notify success")
    signal.signal(signal.SIGALRM, handle)
    signal.alarm(300)
    while True:
        if g_val.ExitFlag.value == 1:
            Log.info("NotifyMode exit")
            sys.exit(0)
        time.sleep(30) #(60)
        send.put( common.encodeMsg("agent", "heart beat", "server") )

def HandleMsg():
    ep = Epoll()
    ep.bind_and_connect()
    ep.hanle_event()

def SigHandler(signum, stack_frame):
    g_val.ExitFlag.value = 1

if __name__ == "__main__":
    g_val = common.Agent()
    recv = multiprocessing.Queue()
    send = multiprocessing.Queue()
    pw = multiprocessing.Process(target=HandleMsg)
    pr = multiprocessing.Process(target=NotifyMode)
    pw.start()
    pr.start()
    with open("/var/run/wechat_agent_pr.pid", 'w') as f:
        f.write(str(pw.pid))
    with open("/var/run/wechat_agent_pw.pid", "w") as f:
        f.write(str(pr.pid))    
    signal.signal(signal.SIGINT, SigHandler)
    if not pw.is_alive() and not pr.is_alive():
        Log.info("main process exit")
        sys.exit(0)
    #pw.join()
    #pr.join()
