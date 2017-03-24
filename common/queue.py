#!/usr/bin/python 
#encoding=utf-8

from collections import deque
import multiprocessing
from msg import Message
from common import Log

class WorkJobQueue(object):
	__instance = None
	def __new__(cls, *args, **kwd):
		if WorkJobQueue.__instance is None:
			WorkJobQueue.__instance = object.__new__(cls, *args, **kwd)
		return WorkJobQueue.__instance

	def __init__(self):
		self.size = 0
		self.lock = multiprocessing.Lock()
		self.Queue = deque()

	def SubmitJob(self, msg):
		with self.lock:
			self.Queue.append({msgid:msg})
			self.size = self.size + 1
	
	def PopJob(self):
		with self.lock:
			if self.size > 0:
				msg = self.Queue.popleft()
				self.size = self.size - 1
				return True, msg
			else:
				return False, None

g_JobQueue = WorkJobQueue()
