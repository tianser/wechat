#!/usr/bin/python2.7 
#encoding=utf-8 

import urllib
import urllib2 
import json
import ConfigParser
from multiprocessing import Process,Queue,Pool, Manager, Value, Array
import commands

import logging
import logging.config 

logging.config.fileConfig('./log.conf')
Log = logging.getLogger('wechat')
cf = ConfigParser.ConfigParser()

def sh_cmd(cmd):
	(status, output) = commands.getstatusoutput(cmd)
	if status == 0:
		return status, output
	else:
		return status, "process failed"

class Agent(object):
	def __init__(self, ConfigFile='./agent.ini'):
		self.ConfigFile = ConfigFile 
		self.NotifyFlag = Value('i', 1)
		self.ExitFlag   = Value('i', 0)
		cf = ConfigParser.ConfigParser()
		cf.read(self.ConfigFile)
		self.ServerIp   = cf.get("server", "ip")
		self.Ip 		= cf.get("agent", "myip")
		self.MyPort     = cf.get("agent", "myport")

class Global(object):
	def __init__(self, configFile='./wechat.ini'):
		self.configFile=configFile
		self.IdFlag = Value('i', 0)
		self.updateconfig = Value('i', 0)
		self.ExitFlag   = Value('i', 0)
		self.whiteName= {}
    
	def ParserArg(self):
		cf = ConfigParser.ConfigParser()
		cf.read(self.configFile)
		self.member = cf.get("auto_reply", "member").split(";") #list

	def GetWhiteName(self):
		cf = ConfigParser.ConfigParser()
		cf.read(self.configFile)
		self.regions = cf.get("client_region", "region").split(";")
		for region in self.regions:
			self.whiteName[region] = cf.get("client_region", region+"_ip")

