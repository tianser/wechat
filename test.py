#!/usr/bin/python2.7
#encoding=utf-8

import urllib
import urllib2
import json

def Mypost(url, params, jsonfmt=True, optional_headers={}):
    url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit?pass_ticket=fi19bhFsGmapf5dC7fHH%2FL5Cxce7d1Bx4zUZn8x9gxtERpfZ0M9UTEKtGJ1nfRsx&skey=@crypt_499327cc_faa26d411ce94727d8e2646fc3ec0a2d&r=1476243916"
    params = "{'Baserequest': {'Sid': u'TcDBrgcI2Gn1yiDL', 'Skey': u'@crypt_499327cc_faa26d411ce94727d8e2646fc3ec0a2d', 'DeviceID': 'e411690935466344', 'Uin': 640393921}}"
    if jsonfmt:
        print url 
        print params
        request = urllib2.Request(url=url, data=json.dumps(params))
        request.add_header('Content-Type', 'application/json; charset=UTF-8')
    else:
        request = Request(url=url, data=urllib.urlencode(params))
    try:
        response = urllib2.urlopen(request, timeout=10)
        content = response.read()
        code = response.getcode()
        response.close()
    except urllib2.URLError, e:
        print e.code
    print code
    if content == '': 
        print "recv empty"
    return content

if __name__ == "__main__":
	url="xx"
	params="xx"
	rt=Mypost(url, params)
	print rt
