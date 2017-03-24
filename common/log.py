import logging
import logging.config 
import ConfigParser
import sys
reload(sys)
sys.setdefaultencoding('utf8')

sys.path.append('./third-pkg')

print sys.path
import coloredlogs 


logging.config.fileConfig('./log.conf')
Log = logging.getLogger('wechat')
cf = ConfigParser.ConfigParser()
cf.read('./wechat.ini')
log_level = cf.get("debug", "level")
coloredlogs.install(level=log_level)

