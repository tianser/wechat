#!/usr/bin/python 
#encoding=utf-8

import queue  
import singleton 

class BaseWork(singleton.Singleton):
	def __init__(self):
		self.Queue = queue.g_JobQueue 
	
	def work(self):
		pass

#g_DealWork = DealWork()
