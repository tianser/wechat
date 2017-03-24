#!/usr/bin/python 
#encoding=utf-8

import socket
from msg.ring_queue import CircularBuffer
from common.log import Log

class BaseSocket(object):
	def __init__(self):
		self.Socket   = None 	#Socket Objects
		self.SocketType = -1	# 0 监听socket， 1 通信socket
		self.SocketStatus = -1	#0关闭，1 打开 2 连接中，3 已连接 ，4 错误 
		self.SocketAttr = -1
		self.Connection = None
		self.PeerIp  = None
		self.PeerPort= 0
		self.RecvBuf = CircularBuffer(102400)		#list，存放RingBuf
		self.SendBuf = CircularBuffer(102400)		#list，存放RingBuf
		self.AdvanceEpoll = None
		self.IOEvents = None
		
	"""
	def test(self):
		Log.error("test log")
	"""
	def SetNoBlock(self):
		if self.Socket:
			self.setblocking(0)
			return True
		else:
			return False

	def OpenSocketAsServer(self, localIP, port):
		if self.Socket:
			self.Socket.close()
		try:
			self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
			self.Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.Socket.bind((localIP, port))
			self.Socket.listen(10)
			self.Socket.setblocking(0)
		except socket.error as msg:
			Log.error("socket error, msg: %s" % msg)
			return False

		self.SocketType = 0
		self.SocketStatus = 1
		return True
	
	def SetEpollObj(self, nEpoll):
		self.AdvanceEpoll = nEpoll

	def ReadEvent(self, fd):
		if self.SocketType == 0 and fd == self.Socket.fileno():
			try:
				newSocket, addr = self.Socket.accept()
			except socket.error as msg:
				Log.error("socket accept error; msg:%s" % msg)
				return None
			#白名单认证
			if not g_server.IsWhiteName(add[0]):
				newSocket.close()
				Log.error("unkown ip(%s) connected, close it" % add[0])
				return None
			Log.info("new connection from %s:%d; Fd=%d" %(addr[0], addr[1], fd))
			#新生成一个socket实例
			OnAccept(newSocket, addr)
		else:
			#ReadSession = g_sessions.get(fd)
			#err = ReadSession.Socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
			err = self.Socket.getsockopt(socket.SOL_SOCKET,socket.SO_ERROR)
			if err != 0:
				Log.error("getsockopt error %s", _strerror(err))
			else:
				OnRead()
	
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
			Log.error("socket set-no-block error, fd: %d" % NewSession.Socket.fileno())
			NewSession.CloseSocket()       
			return None
		g_EpollCtl.RegistEvent(NewSession, select.EPOLLIN | select.EPOLLOUT)   
		#self.nSession[NewSession.Socket.fileno()] = NewSession 
		g_Sessions.add(NewSession)
		return True

	
	def OnRead(self):
		tataldata = ''
		while True: 
			try:
				data = self.Socket.recv(64)
				if not data:
					Log.error("socket read error; addr:%s" % self.PeerIp)
					CloseSocket()
					break
				else:
					tataldata += data
			except socket.error, msg:
				if msg.errno != errno.EAGAIN:
					return False
				else:
					Log.debug("recv msg: %s" % tataldata)
					self.RecvBuf.Write(tataldata, len(tataldata))
					return True
	
	def WriteEvent(self):
		err = self.Socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
		if err != 0:
			Log.error("getsockopt error %s", _strerror(err))
			return None
		while self.SendBuf.Space() > 0:
			data = self.SendBuf.Read(64)
			if not data:
				break
			try:
				self.Socket.sendall(data)
			except socket.error, e:
				Log.error("socket send error; cause:%s" % _strerror(err))
				self.SendBuf.WriteFromHead(data, len(data))
				break
		self.ChangeWriteEvent()
		return None
	
	def ChangeWriteEvent(self):
		if self.SendBuf.Space() > 0:
			g_EpollCtl.RegistEvent(self, select.EPOLLOUT)
		else:
			g_EpollCtl.RemoveEvent(self, select.EPOLLOUT)


	def Connect(self, RemoteIP, nport):
		Log.info("Connect %s:%d\n" % (RemoteIP, nport))
		if not RemoteIP:
			Log.error("invaild IP: %s" % RemoteIP)
			return False
		if nport <= 0:
			Log.error("invaild port: %d" % nport)
			return False
		if self.SocketType != 1:
			Log.error("connect server; socketType: %d " % self.SocketType)
			return False
		if not self.Socket and SocketStatus != 1:
			Log.error("socket not open")
			return False
		try:
			self.Socket.connect((RemoteIP, nport))
		except socket.error as msg:
			Log.error("socket connect error; %s" % msg)
			CloseSocket()	
			return False
		self.SocketStatus = 3 
		return Connected()

	def Connected(self):
		self.PeerIp, self.PeerPort = self.Socket.getsockname()
		if self.PeerIp == "127.0.0.1":
			Log.error("tcp self Connection, close it; socketFd = %d" % self.Socket.fileno())
			CloseSocket()	
			return False
		return True

	def ERREvent(self):
		if not self.Socket:
			Log.error("Socket error,cannot close it;")
			return False
		g_EpollCtl.DeleteEvent(self)
		g_sessions.Del(self.Socket.fileno())
		CloseSocket()

	def OnConnected(self):
		return True	

				
	def CloseSocket(self):
		if not self.Socket:
			Log.error("Socket error,cannot close it")
			return False
		self.Socket.close()
		self.SocketStatus = 0
		self.SocketType = -1
		return True


