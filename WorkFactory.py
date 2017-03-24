#!/usr/bin/python 
#encoding=utf-8

from common import BaseWork
from common import Log
from msg import heart

class WorkInstance(BaseWork):
	def __init__(self):
		BaseWork.__init__(self)
		self.msgInstance = {}
		self.msgInstance = {1:heart()}

	def work(self):
		hasJob, msg_dict = self.Queue.PopJob()	
		if hasJob:
			msgId = msg_dict.keys()[0]
			msg   = msg_dict.values()[0]
			#@TODO	
			if msgId == 1:
				instance= heart()
				heart2.ParseFromString(msg.Getbody())
				
			else:
				Log.error("msgId error !")


g_WorkInstance = WorkInstance()
