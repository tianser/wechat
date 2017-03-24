#!/usr/bin/python 
#encoding=utf-8

class Singleton(object):
	__instance = None
	def __init__(self):
		pass 

	def __new__(cls, *args, **kwd):
		if Singleton.__instance is None:
			Singleton.__instance = object.__new__(cls,  *args, **kwd)

		return Singleton.__instance


