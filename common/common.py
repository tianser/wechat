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
import signal
import sys
reload(sys)
sys.setdefaultencoding('utf8')

sys.path.append("./third-pkg")
import coloredlogs
logging.config.fileConfig('./log.conf')
Log = logging.getLogger('wechat')
cf = ConfigParser.ConfigParser()
cf.read('./wechat.ini')
log_level = cf.get("debug", "level")
coloredlogs.install(level=log_level)

def sh_cmd(cmd):
	(status, output) = commands.getstatusoutput(cmd)
	if status == 0:
		return status, output
	else:
		return status, "process failed"

class SigHandle(object):
	"""python signal wrapper"""

	def __init__(self):
		"""Initialize signal
		:param Flag: thread Flag 
		:returns: None
		"""
		signal.signal(signal.SIGINT, self.handler)
		self.Flag = 0 

	def handler(self, signum, frame):
		"""receive SIGINT,and execute this function
		alter Flag	
		"""
		self.Flag = 1
		Log.info("signal recv signum: %d" % signum)

class Agent(object):
	def __init__(self, ConfigFile='./agent.ini'):
		"""Initialize Agent configure file 
		:param NotifyFlag: agent do Timer Task or not 
		:param ExitFlag:   multiprocessing exit or not
		:Param ServerIp:   wechat server ip address 
		:param Ip:         agent ip address 
		:param Myport:     agent tcp port 
		:returns: None
		"""
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
		"""Initialize wechat Server configure file 
		:param IdFlag: wechat send msg to group or my wechat friends setted in configure file 
		:param updateconfig: discard now 
		:param ExitFlag: multiprocessing exit or not 
		:param whiteName: agent region and ip
		"""
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
		"""read configure file to initialize whiteName
		"""
		cf = ConfigParser.ConfigParser()
		cf.read(self.configFile)
		self.regions = cf.get("client_region", "region").split(";")
		for region in self.regions:
			self.whiteName[region] = cf.get("client_region", region+"_ip")

def encodeMsg(fromTo, request, sendTo):
	"""encode msg to json
	:param fromTo: wechat receive from 
	:param request: request content 
	:param sendTo: agent on the region
	:returns None
	"""
	encode = {}
	encode["fromTo"] = fromTo   #Í«≥∆
	encode["content"] = request
	encode["sendTo"]  = sendTo  #«¯”Ú
	return json.dumps(encode)


