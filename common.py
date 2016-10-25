#!/usr/bin/python2.7 
#encoding=utf-8 

import urllib
import urllib2 
import json
import qrcode
import ConfigParser
from multiprocessing import Process,Queue,Pool, Manager, Value, Array
import commands

import logging
import coloredlogs
import logging.config 

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

def Agent(object):
	def __init__(self, ConfigFile='./agent.ini'):
		self.ConfigFile = ConfigFile 
		self.NotifyFlag = Value('i', 1)
        self.ExitFlag   = Value('i', 0)
		cf = ConfigParser.ConfigParser()
		cf.read(self.ConfigFile)
		self.ServerIp   = cf.get("server", "ip")
		self.MyIp 		= cf.get("agent", "myip")
		self.Myport     = cf.get("agent", "myport")

class Global(object):
	def __init__(self, configFile='./wechat.ini'):
		self.configFile=configFile
		self.IdFlag = Value('i', 0)
		self.updateconfig = Value('i', 0)
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

def _decode_list(data):
	rt = []
	for item in data:
		if isinstance(item, unicode):
			item = item.encode('utf-8')
		elif isinstance(item, list):
			item = _decode_list(item)
		elif isinstance(item, dict):
			item = _decode_dict(item)
		rt.append(item)
	return rt

def _decode_dict(data): 
	rt = {}
	for key, value in data.iteritems():
		if isinstance(key, unicode):
			key = key.encode('utf-8')
		if isinstance(value, unicode):
			value = value.encode('utf-8')
		elif isinstance(value, list):
			value = _decode_list(value)
		elif isinstance(value, dict):
			value = _decode_dict(value)
		rt[key] = value 
	return rt


def _genQRCode(uuid, url='https://login.weixin.qq.com/l/'):
		url = url + uuid
		qr = qrcode.QRCode()
		qr.border = 1
		qr.add_data(url)
		mat = qr.get_matrix()
		for i in mat:
			BLACK = '\033[40m  \033[0m'
			WHITE = '\033[47m  \033[0m'
			print ''.join([BLACK if j else WHITE for j in i])

def _get(url, api=None):
	request = urllib2.Request(url=url)
	request.add_header('Referer', 'https://wx.qq.com/')
	if api == 'webwxgetvoice':
		request.add_header('Range', 'bytes=0-')
	if api == 'webwxgetvideo':
		request.add_header('Range', 'bytes=0-')
	response = urllib2.urlopen(request)
	data = response.read()
	code=response.getcode()
	print code
	return data

def _post(url, params, jsonfmt=True):
	if jsonfmt:
		print url
		print params
		request = urllib2.Request(url=url, data=json.dumps(params))
		request.add_header('Content-Type', 'application/json; charset=UTF-8')
	else:
		request = urllib2.Request(url=url, data=urllib.urlencode(params))
	response = urllib2.urlopen(request)
	content = response.read()
	code = response.getcode()
	print code, content 
	if content == '':
		print "recv empty"
	if jsonfmt:
		return json.loads(content, object_hook=_decode_dict)
	return content

