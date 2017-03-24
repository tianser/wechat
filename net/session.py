#!/usr/bin/python 
#encoding=utf-8

import baseSocket
from msg.message import Message
from common.queue import g_JobQueue 
import multiprocessing
import struct

class Session(baseSocket.BaseSocket):
	def __init__(self):
		#super(Session, self).__init__()
		baseSocket.BaseSocket.__init__(self)
	
	def Reset(self):
		pass	
	
	def Clear(self):
		pass	

	def OnRead(self):
		tataldata = ''
		while True: 
			try:
				data = self.Socket.recv(64)
				if not data:
					Log.error("socket read error; addr:%s" % self.PeerIp)
					CloseSocket()
					return False
				else:
					tataldata += data
			except socket.error, msg:
				if msg.errno != errno.EAGAIN:
					return False
				else:
					Log.debug("recv msg: %s" % tataldata)
					self.RecvBuf.Write(tataldata, len(tataldata))
					break
		while self.RecvBuf.Space() > 16:
			head = self.RecvBuf.Read(16)
			if not head:
				Log.error("RecvBuf get head error")
				g_Sessions.Del(self.Socket.fileno())
				self.CloseSocket()
				break 
			try:
				msgid, totalsize, pbsize, crc = struct.unpack('iiii', head)
			except struct.error as e:
				self.RecvBuf.WriteFromHead(head, len(head))
				break

			if not self.RecvBuf.Space() > totalsize:
				self.RecvBuf.WriteFromHead(head, len(head))
				break
			body = self.RecvBuf.Read(totalsize)
			if not body:
				Log.error("Recvbuf get body error")
				g_Sessions.Del(self.Socket.fileno())
				self.CloseSocket()
				break 
			try:
				pb = struct.unpack(str(pbsize)+'s', body)
			except struct.error:
				self.RecvBuf.WriteFromHead(body, len(body))
				self.RecvBuf.WriteFromHead(head, len(head))
				break
			msg = CreateMessage()		
			msg.SetMsgId(msgid)
			msg.Setbodysize(pbsize)
			msg.Setbody(pb)
			SubmitJob(msg)

	def CreateMessage(self):
		msg = Message()
		msg.SetSession(self)
		return msg

	def SubmitJob(self, msg): 
		g_JobQueue.SubmitJob(msg)	

	#def WriteMsg(self)

class nSession(object):
	__instance = None
	def __new__(cls, *args, **kwd):
		if nSession.__instance is None:
			nSession.__instance = object.__new__(cls, *args, **kwd)
		return nSession.__instance

	def __init__(self):
		self.lock = multiprocessing.Lock()
		self.sessions = {}
	
	def get(self, fd):
		with self.lock:
			if fd in self.sessions.keys():
				return self.sessions[fd]
			else:
				return None

	def add(self, s):
		with self.lock:
			self.sessions[s.Socket.fileno()] = s
	
	def Del(sel, fd):
		with self.lock:
			if fd in self.sessions.keys():
				del self.sessions[fd]

Sessions = nSession()
#g_Sessions=nSession()

