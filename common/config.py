#!/usr/bin/python 
#encoding=utf-8

import ConfigParser
import log
#from common import Log 

class Client(object):
	__instance = None
	def __new__(cls, *args, **kwd):
		if Client.__instance is None:
			Client.__instance = object.__new__(cls, *args, **kwd)
		return Client.__instance

	def __init__(self, ConfigFile='/root/wechat/agent.ini'):
		self.ConfigFile = ConfigFile 
		log.Log.info("wechat client configFile: %s" % ConfigFile)
		cf = ConfigParser.ConfigParser()
		cf.read(self.ConfigFile)
		self.ServerIp   = cf.get("server", "ip")
		self.Ip 		= cf.get("agent", "myip")
		self.MyPort     = cf.get("agent", "myport")

class Global(object):
	__instance = None
	def __new__(cls, *args, **kwd):
		if Global.__instance is None:
			Global.__instance = object.__new__(cls, *args, **kwd)
		return Global.__instance

	def __init__(self, configFile='/root/wechat/wechat.ini'):
		log.Log.info("wechat server configFile: %s" % configFile)
		self.configFile=configFile
		self.whiteName= {}
		cf = ConfigParser.ConfigParser()
		cf.read(self.configFile)
		self.member = cf.get("auto_reply", "member").split(";") #list
		self.localIp = cf.get("server_info", "ip")
		self.port = int(cf.get("server_info", "port"))

		self.regions = cf.get("client_region", "region").split(";")
		for region in self.regions:
			self.whiteName[cf.get("client_region", region+"_ip")] = region

	def IsWhiteName(self, ip):
		if ip not in self.whiteName.keys():
			return False
		else:
			return True

server=Global()
g_client = Client()





