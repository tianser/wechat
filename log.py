#!/usr/local/bin/python2.7 
#encoding=utf-8 

import logging
import logging.config 

logging.config.fileConfig('./log.conf')
Log = logging.getLogger('wechat')
