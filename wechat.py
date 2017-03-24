#!/usr/bin/python 
#encoding=utf-8

from common import Log
from net import g_EpollCtl
from common import server
from common import BaseServer
from net import Session, Sessions
import WorkFactory
import select

class WechatServer(BaseServer):
	def __init__(self):
		BaseServer.__init__(self)
		self._run = True 
		self.DealWork = WorkFactory.g_WorkInstance 

	def Start(self):
		self.AdvanceEpoll = g_EpollCtl
		if not self.OpenSocketAsServer(server.localIp, server.port):
			Log.error("start Server error")
			return None 
	
		print type(g_EpollCtl)
		g_EpollCtl.RegistEvent(self, select.EPOLLIN | select.EPOLLET)	
		newSession = Session()
		newSession.Socket = self.Socket
		newSession.SocketType = self.SocketType
		newSession.SocketStatus = self.SocketStatus
		newSession.IOEvents = select.EPOLLIN | select.EPOLLET
		newSession.AdvanceEpoll = g_EpollCtl
		Sessions.add(newSession)
		while self._run:
			g_EpollCtl.HandleMessage(self.Socket.fileno())
			if self.DealWork:
				self.DealWork.work()
		Log.info("WechatServer end !")
			

	
	def Stop(self):
		pass

if __name__ == "__main__":
	app = WechatServer()
	print type(app)
	app.Start()
