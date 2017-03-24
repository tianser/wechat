#!/usr/bin/python 
#encoding=utf-8

from net import BaseSocket
from net import Session
from net import Sessions
from net import g_EpollCtl
#from common import Log
import log
import select

class BaseServer(BaseSocket):
	def __init__(self):
		BaseSocket.__init__(self)
		self.nSession = {}

	def OnAccept(self, NewSocket, PeerInfo):
		NewSession = Session()			
		NewSession.Socket = NewSocket 
		NewSession.Connection = NewSocket
		NewSession.SocketType = 1
		NewSession.SocketStatus = 3
		NewSession.PeerIp = PeerInfo[0]
		NewSession.PeerPort = PeerInfo[1]
		NewSession.IOEvents = select.EPOLLIN

		if not NewSession.SetNoBlock():
			log.Log.error("socket set-no-block error, fd: %d" % NewSession.Socket.fileno())
			NewSession.CloseSocket()
			return None

		g_EpollCtl.RegistEvent(NewSession, select.EPOLLIN | select.EPOLLOUT)
		#self.nSession[NewSession.Socket.fileno()] = NewSession	
		g_Sessions.add(NewSession)
		return True


