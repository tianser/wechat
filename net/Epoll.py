#!/usr/bin/python 
#encodin=utf-8

from common import Log
import session #g_Sessions
import select

class Epoll(object):
	__instance = None 
	def __new__(cls, *args, **kwd):
		if Epoll.__instance is None:
			Epoll.__instance = object.__new__(cls, *args, **kwd)
		return Epoll.__instance

	def __init__(self):
		self.Epoll = None 
		self.MaxFd = 0
		self.EpollEventTimeout = 0
		self.Epoll = select.epoll()

	def RegistEvent(self, BSocket, Events):
		self.Epoll.register(BSocket.Socket.fileno(), Events)

	def RemoveEvent(self, BSocket, Events):
		newEvents = BSocket.IOEvents & (~Events)
		self.Epoll.modify(BSocket.Socket.fileno(), Events)

	def DeleteEvent(self, BSocket):
		self.Epoll.unregister(BSocket.Socket.fileno())

	def GetEpollFd(self):
		return self.Epoll

	def HandleMessage(self, listenfd):
		nEvents = self.Epoll.poll(1)	
		for fd, event in nEvents:
			session = session.g_Sessions.get(listenfd)
			if not Socket:
				Log.error("not find ioevents fd from g_Sessions")
				return None

			if event & select.EPOLLIN:  #READ
				session.ReadEvent(fd)	
			elif event & select.EPOLLOUT:	#Write
				session.ReadEvent(fd)	
			elif event & select.EPOLLERR:   #ERROR
				session.ERREvent(fd)	
			elif event & select.EPOLLHUP:   #client close fd
				session.ERREvent()	
			else:
				Log.error("it's not found ioevents %d\n", event)

g_EpollCtl = Epoll()
