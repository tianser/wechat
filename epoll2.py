#!/usr/bin/python2.7 
#encoding=utf-8 

import socket, select 
from multiprocessing import Process,Queue,Pool, Manager
#import Queue 
from log import Log as Log
#from multiprocessing import Queue, Manager, Process
import time
import common
import errno

class Epoll(object):
	def __init__(self, port=9999):
		self.address = ("0.0.0.0", port)
		try:
			self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error as msg:
			Log.error("socket error, %s", msg)
			sys.exit(0)

		self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
		self.timeout = 10
		self.recv_message_queues = {}
		self.send_message_queues = {}	#ip： msg
	
	def bind_and_listen(self):
		try:
			self.server_socket.bind(self.address)
			self.server_socket.listen(10)
			self.server_socket.setblocking(0)
		except socket.error as msg:
			self.server_socket.close()
			self.server_socket = None
			Log.error("bind or listen error, %s", msg)
			sys.exit(0)
	
	def	epoll_init(self):
		self.epoll = select.epoll()
		self.epoll.register(self.server_socket.fileno(), select.EPOLLIN)
		self.fd_to_socket = {self.server_socket.fileno():self.server_socket,}
		self.fd_to_ip = {}
	
	def handle_event(self, recv, send): 
		while True:
			events = self.epoll.poll(self.timeout)
			if not events:
				continue
			for fd, event in events:
				socket = self.fd_to_socket[fd]
				#EPOLLIN
				if event & select.EPOLLIN:
					if socket == self.server_socket:	#监听socket
						connection, address = self.server_socket.accept()
						connection.setblocking(0)
						#注册新连接fd到待读事件集合
						if address[0] not in g_val.WhiteName:	#不在白名单里面，T掉
							self.epoll.register(connection.fileno, select.EPOLLHUP)
						else:
							print "whiteName find it"
							self.epoll.register(connection.fileno(), select.EPOLLIN | select.EPOLLET)
							self.recv_message_queues[connection] = Queue()
						self.fd_to_socket[connection.fileno()] = connection 
						self.fd_to_ip[connection.fileno()] = address[0]
					else: 								#客户端发送数据的socket
						print "read data"
						all_data = ""
						while True:
							try:
								data = socket.recv(1024)	#阻塞
								all_data = all_data + data
								if not data:
									self.epoll.unregister(socket)
									socket.close()
									del fd_to_ip[fd]
									del fd_to_socket[fd]
									break
							except socket.error, error:
								if error.errno == errno.EAGAIN:
									self.epoll.modify(fd, select.EPOLLOUT)	#修改文件描述符标记
									break
								else:
									self.epoll.unregister(socket)
									del fd_to_ip[fd]
									del fd_to_socket[fd]
									socket.close()
						print "all_data: ", all_data	
						if all_data:
							Log.info("recv from: %s, msg: %s"%\
									(all_data, socket.getpeername()) )
							recv.put(all_data)		 #发给其他进程
				elif event & select.EPOLLOUT:
					while True:
						if not send.empty():
							send_msg = send.get(True)
							info = send_msg.split(":")	
							if info[0] in self.fd_to_ip.values():
								for key, value in self.fd_to_ip.items():
									if key==fd and value == info[0]:
										Log.info("send msg:%s to %s " % (info[1], self.fd_to_socket[fd].getpeername()))
										self.fd_to_socket[fd].send(info[1])	
										break
							else:
								recv.put(("%s is lost"%info[0]))
								break
						else:
							self.epoll.modify(fd, select.EPOLLIN)
							break
				elif event & select.EPOLLHUP:
					self.epoll.unregister(fd)
					fd_to_socket[fd].close()
					del fd_to_ip[fd]
					del fd_to_socket[fd]

	def epoll_destroy(self):
		self.epoll.unregister(self.server_socket.fileno())
		self.epoll.close()
		self.server_socket.close()

def process1(recv, send):
	print "process1"
	epoll = Epoll()
	epoll.bind_and_listen()
	epoll.epoll_init()
	epoll.handle_event(recv, send)
	print "process1---"
	epoll.epoll_destroy()

def process2(recv, send):
	while True:
		if not recv.empty():
			msg = recv.get_nowait()
			Log.info("........recv: %s" %msg)
		else:
			Log.info(" recv no")
		send.put("127.0.0.1:xxxx")
		time.sleep(3)


if __name__ == "__main__":	
	manager = Manager()
	recv = manager.Queue()
	send = manager.Queue()
	g_val = common.Global()
	g_val.GetWhiteName()
	p = Pool(3)
	#p = Process(target=process1, args=(recv, send,))
	#p.start()
	#p2 = Process(target=process2, args=(recv, send,))
	#p2.start()

	pw = p.apply_async(process1, args=(recv, send))
	pr = p.apply_async(process2, args=(recv, send))
	p.close()
	p.join()
