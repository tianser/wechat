#!/usr/bin/python2.7
#encoding=utf-8

import qrcode 
import urllib 
import urllib2 
import cookielib 
import time
import os 
import sys
import random
import re
import xml.dom.minidom
from lxml import html
import json

from log import Log as Log
import common
import test

class WebWeChat(object):
	def __init__(self):
		self.DEBUG = False 
		self.uuid  = ''
		self.base_uri = ''
		self.redirect_uri = ''
		self.uin = ''
		self.sid = ''
		self.skey = ''
		self.pass_ticket = ''
		self.deviceId = 'e' + repr(random.random())[2:17]
		self.baseRequest = {}
		self.synckey = ''
		self.SyncKey = []
		self.User = []
		self.MemberList = []
		self.ContactList = []	#好友列表
		self.GroupList   = []	#群列表
		self.GroupMemberList = [] #群成员 
		self.PublicUsersList = [] #公众号/服务号
		self.SpecialUsersList = [] #特殊账号
		self.autoReplyMode	  = False 
		self.syncHost = ''
		self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) \
			Chrome/48.0.2564.109 Safari/537.36'
		self.interactive = False 
		self.autoOpen = False 
		self.saveFolder = os.path.join(os.getcwd(), 'saved')
		self.saveSubFolders = {'webwxgeticon':'icons','webwxgetheading':'headimgs','webwxgetmsgimg':'msgimgs',
		'webwxgetvideo':'videos', 'webwxgetvoice':'voices', '_showQRCodeImg':'qrcodes'}
		self.appid = 'wx782c26e4c19acffb'   #web微信 appId
		self.lang = 'zh_CN'
		self.lastCheckTs = time.time()
		self.memberCount = 0
		self.SpecialUsers = ['newsapp', 'fmessage', 'filehelper', 'weibo', 'qqmail', 'fmessage', 'tmessage', 
						 'qmessage', 'qqsync', 'floatbottle', 'lbsapp', 'shakeapp', 'medianote', 'qqfriend', 
						 'readerapp', 'blogapp', 'facebookapp', 'masssendapp', 'meishiapp', 'feedsapp','voip',
						 'blogappweixin', 'weixin', 'brandsessionholder', 'weixinreminder', 
						 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'officialaccounts', 'notification_messages',
						 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'wxitil', 'userexperience_alarm',
						 'notification_messages']
		self.TimeOut = 20   #每20s同步一次消息
		self.media_count = -1
		self.cookie = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie))
		opener.addheader = [('User-agent', self.user_agent)]
		urllib2.install_opener(opener)
	
	def synccheck(self):
		params = {
				'r': int(time.time()),
				'sid': self.sid,
				'uin': self.uin,
				'skey': self.skey,
				'deviceid': self.deviceId,
				'synckey': self.synckey,
				'_': int(time.time()),
		}
		url = 'https://' + self.syncHost + \
			  '/cgi-bin/mmwebwx-bin/synccheck?' + urllib.urlencode(params)
		data = common._get(url)
		print "synccheck: ", data
		pm = re.search(r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}', data)
		retcode = pm.group(1)
		selector = pm.group(2)
		return [retcode, selector]

	def testsynccheck(self):
		SyncHost = ['webpush.weixin.qq.com', 'webpush2.weixin.qq.com', 'webpush.wechat.com', \
				    'webpush1.wechat.com', 'webpush2.wechat.com'] #'webpush1.wechatapp.com',]
		for host in syncHost:
			self.syncHost = host 
			[retcode, selector] = self.synccheck()
			if retcode == '0':
				return True
		return False

	def WebWeChatSync(self):
		url = self.base_uri + '/webwxsync?sid=%s&skey=%s&pass_ticket=%s' % \
				(self.sid, self.skey, self.pass_ticket)
		params = {
			'BaseRequest': self.BaseRequest,		
			'SyncKey': self.SyncKey,
			'rr': ~int(time.time())
		}
		dic = common._post(url, params)
		if dic['BaseResponse']['Ret'] == 0:
			self.SyncKey = dic['SyncKey']
			self.synckey = '|'.join([str(keyVal['Key'])+'_'+str(keyVal['Val']) 	\
				for keyVal in self.SyncKey['List']])
		return dic

	def getUserRemarkName(self, id):
		name = 'unknow group' if id[:2] == '@@' else 'unknow'
		if id == self.User['UserName']:
			return self.user['NickName']
		if id[:2] == '@@': 				#group
			name = self.getGroupName(id)
		else:
			#特殊账号
			for member in self.SpecialUsersList:
				if member['UserName'] == id:
					name = member['RemarkName'] if member['RemarkName'] else member['NickName']
			#公众号或服务号
			for member in self.PublicUsersList:
				if member['UserName'] == id:
					name = member['RemarkName'] if member['RemarkName'] else member['NickName']
			#contact
			for member in self.ContackList:
				if member['UserName'] == id:
					name = member['RemarkName'] if member['RemarkName'] else member['NickName']
			for member in self.GroupMemberList:
				if member['UserName'] == id:
					name = member['DisplayName'] if member['DisplayName'] else member['NickName']
		if name=='未知群' or name=='陌生人':
			Log.debug("msg from: %s ", name)
		return name

	def handleMsg(self, r):
		for msg in r['AddMsgList']:
			msgType = msg['MsgType']
			From = self.getUserRemarkName(msg['FromUserName'])
			content = msg['Content'].replace('&lt;', '<').replace('&gt;', '>')
			msgid = msg['MsgId']
			
			#TODO 对发信息的人进行过滤
			if msgType == 1 :
				raw_msg = {'raw_msg': msg}
				Log.info("msg from :%s, content:%s"%(From, content))
				self.sendMsg(From, "hi==========")
				#TODO 在此动态加载配置文件
				#暂时先将消息存入文件,并设置自动回复

	def listenMsgMode(self):
		Log.debug("listenMsg start")
		if not testsynccheck():
			Log.error("syncHost test failed")
		playWeChat = 0
		redEnvelope = 0
		while True:
			self.lastCheckTs = time.time()
			[retcode, selector] = self.synccheck()
			Log.debug('retcode: %s, selector: %s' % (retcode, selector))
			if retcode == '1100':
				Log.info("your phone logout wechat, bye")
				break 
			if retcode == '1101':
				Log.info("you login WebWeChat other,bye")
				break
			elif retcode == '0':
				if selector == '2':
					r = self.WebWeChatSync()
					if r is not None:
						self.handleMsg(r)
				elif selector == '6':
					#TODO 
					redEnvelope += 1
					Log.info("recv redEnvelope %d times" % redEnvelope)
				elif selector == '7':
					playWeChat += 1
					Log.info("phone send msg %d times" % playWeChat)
					r = self.WebWeChatSync()
				elif selector == '0':
					time.sleep(3)
			if (time.time() - self.lastCheckTs) <= 20:
				time.sleep(time.time() - self.lastCheckTs)

	def start(self):
		Log.debug("WebWeChat start")
		while True:
			if self.getUUID():
				Log.debug("getuuid success")
			else:
				Log.error("getuuid failed; try again")
				continue
			common._genQRCode(self.uuid, 'https://login.weixin.qq.com/l/')		
			print '请使用微信扫描二维码以登录'
			break

		while True:
			if 201 == self.waitForLogin():
				print '扫描成功，请在手机上点击确认以登录'
				break
			else:
				print '扫描失败'
				time.sleep(1)
		while True:
			if 200 == self.waitForLogin(0):
				print '手机端确认登录成功'
				break
			else:
				print '手机端确认登录失败'
				time.sleep(1)

		if not self.login():
			print 'login failed'
			sys.exit()
		print "login success"
		if self.wechatInit() and self.wechatStatusNotify() and self.wechatGetContact() :
			Log.info("friendCount: %d" % self.MemberCount)
			Log.info("GroupConuts: %d \n PublicUsers: %d " % (len(self.GroupList), len(self.PublicUsersList)))
	
		#该进程处理接收的消息
		listenProcess = multiprocessing.Process(target=self.listenMsgMode)
		listenProcess.start()
		while True:
			time.sleep(20)
			#self.sendMsgToAll(word)
			#self.sendMsg(name, word)
	
	def sendMsg(self, name, word, isfile=False):
		id = self.getUSerID(name)
		if id:
			if self.PostMsg(word, id):
				Log.debug("send msg to %s success"%name)
			else:
				Log.error("send msg to %s failed, content: %s" %(name, word))
		else:
			Log.error("account[%s] not exist" % name)

	def PostMsg(self, word, to='filehelper'):
		url = self.base_uri + '/webwxsendmsg?pass_ticket=%s' % (self.pass_ticket)
		clientMsgId = str(int(time.time()*1000)) + str(random.random())[:5].replace('.', '')
		params = {
			'BaseRequest': self.BaseRequest,		
			'Msg':{
				"Type": 1,
				"Content": self._transcoding(word),
				"FromUserName": self.User["UserName"],
				"ToUserName": to,
				"LocalID": ClientMsgId,
				"ClientMsgId": clientMsgId
			}
		}
		headers = {'content-type':'application/json;charset=UTF-8'}
		data = json.dumps(params, ensure_ascii=False).encode('utf8')
		r = request.post(url, data=data, headers=headers)
		dic = r.json()
		return dic['BaseResponse']['Ret'] == 0

	def wechatInit(self):
		Log.info("base_uri: %s" % self.base_uri)
		url = self.base_uri + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' %  \
			(self.pass_ticket, self.skey, int(time.time()))
		params = {
			'Baserequest': self.BaseRequest	
		}
		dic = test.Mypost(url, params)
		self.SyncKey = dic['SyncKey']
		self.User = dic['User']
		#synckey for synccheck 
		self.synckey = '|'.join([str(keyVal['Key'])+'_'+str(keyVal['Val']) for keyVal in self.SyncKey['List']])
		return dic['BaseResponse']['Ret'] == 0

	def wechatStatusNotify(self):
		url = self.base_uri + '/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % (self.pass_ticket)
		params = {
			'BaseRequest': self.BaseRequest,
			'Code': 3,
			"FromUserName": self.User['UserName'],
			"ToUserName": self.User['UserName'],
			"ClientMsgId": int(time.time()),
		}
		print "notify"
		dic = common._post(url, params)
		return dic['BaseResponse']['Ret'] == 0

	def wechatGetContact(self):
		SpecialUsers = self.SpecialUsers 
		url = self.base_uri +'/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s'%	\
				(self.pass_ticket, self.skey, int(time.time()))
		print "getcontace"
		dic = common._post(url, {})
		self.MemberCount = dic['MemberCount']
		self.MemberList  = dic['MemberList']
		ContactList      = self.MemberList[:]
		GroupList 		 = self.GroupList[:]
		PublicUsersList  = self.PublicUsersList[:]
		SpecialUsersList = self.SpecialUsersList[:]

		for i in xrange(len(ContactList)-1, -1, -1):
			Contact = ContactList[i]
			if Contact['VerifyFlag'] & 8 != 0: #公众号，服务号 
				ContactList.remove(Contact)
				self.PublicUsersList.append(Contact)
			elif Contact['UserName'] in SpecialUsers: 	#特殊号 
				ContactList.remove(Contact)
				self.SpecialUsersList.append(Contact)
			elif Contact['UserName'].find('@@') != -1: 	#群号 
				ContactList.remove(Contact)
				self.GroupList.append(Contact)
			elif Contact['UserName'] == self.User['UserName']: #自己
				ContactList.remove(Contact)
		self.ContactList = ContactList
		return True

	def wechatGetGroupList(self):
		url = self.base_uri + '/webwxbatchgetcontact?type=ex&r=%s&pass_ticket=%s' \
				%( int(time.time()), self.pass_ticket)
		params = {
			'BaseRequest': self.BaseRequest,
			'Count': len(self.GroupList),
			'List' : [{'UserName':g['UserName'], "EncryChatRoomId":""} for g in self.GroupList]
		}
		dic = common._post(url, params)

		ContactList = dic['ContactList']
		ContactCount = dic['Count']
		self.GroupList = ContactList
		for i in xrange(len(ContactList)-1, -1, -1):
			Contact = ContactList[i]
			MemberList = Contact["MemberList"]
			for member in MemberList:
				self.GroupMemberList.append(member)
		return True
	
	def login(self):
		data = common._get(self.redirect_uri)
		doc = xml.dom.minidom.parseString(data)
		root = doc.documentElement
		for node in root.childNodes:
			if node.nodeName == 'skey':
				self.skey = node.childNodes[0].data
			elif node.nodeName == 'wxsid':
				self.sid = node.childNodes[0].data 
			elif node.nodeName == 'wxuin':
				self.uin = node.childNodes[0].data 
			elif node.nodeName == 'pass_ticket':
				self.pass_ticket = node.childNodes[0].data 
		print self.pass_ticket
		if '' in (self.skey, self.sid, self.uin, self.pass_ticket):
			return False 
		self.BaseRequest = {
			'Uin': int(self.uin),
			'Sid': self.sid,
			'Skey': self.skey,
			'DeviceID': self.deviceId,
		}
		return True
			
	def waitForLogin(self, tip=1):
		time.sleep(tip)
		url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s'  \
			% (tip, self.uuid, int(time.time()))
		data = common._get(url)
		pm = re.search(r'window.code=(\d+);', data)
		code = pm.group(1)
		if code == '201':
			return 201 
		elif code == '200':
			print "waitForLogin:", data
			pm = re.search(r'window.redirect_uri="(\S+?)";', data)
			r_uri = pm.group(1) + '&fun=new&version=v2'
			self.redirect_uri = r_uri 
			self.base_uri = r_uri[:r_uri.rfind('/')]
			return 200
		elif code == '408':
			Log.debug('login timeout')
		else:
			Log.error('login exception occur')
		return None

	def getUUID(self):
		url = 'https://login.weixin.qq.com/jslogin'
		params = {
			'appid': self.appid,
			'fun': 'new',
			'lang': self.lang,
			'_': int(time.time()),
		}
		data = common._post(url, params, False)
		#regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
		regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"' 
		pm = re.search(regx, data)
		if pm:
			code = pm.group(1)
			self.uuid = pm.group(2)
			return code == '200'
		return False

if __name__ == "__main__":
	g_val = common.Global()
	g_val.ParserArg()
	Wechat = WebWeChat()
	Wechat.start()


