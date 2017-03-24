#!/usr/bin/python 
#encoding=utf-8

class Message(object):
	def __init__(self):
		self.HeadSize = 16  #消息头固定16字节
		self.MsgId  = -1
		self.bodysize = 0
		self.body = None
		self.Session = None
	
	def SetMsgId(self, Id):
		self.MsgId = Id

	def GetMsgId(self):
		return self.MsgId

	def Setbodysize(self, size):
		self.bodysize = size 
	
	def Getbodysize(self):
		return self.bodysize

	def Setbody(self, body):
		self.body = body 
	
	def Getbody(self):
		return self.body 

	def SetSession(self, session):
		self.Session = session 
	
	def GetSession(self):
		return Session

	#def Decode(self):


