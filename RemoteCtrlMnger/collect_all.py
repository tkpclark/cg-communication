#encoding:utf-8
import subprocess
from db import *
import ast
import os
import sys
import time
import urllib2
from config import *
from logging.handlers import RotatingFileHandler
from config import *
import logging
import threading

def get_net_element():
	sql = "select number from lich_network_element"
	try:
		mysql = Mydb(host, user, password)
		mysql.selectDb(db_name)
		re = mysql.queryAll(sql)
	except Exception, e:
		logging.info(e)
	mysql.close()
	return re

def routin():
	net_elements = get_net_element()
	for net_element in net_elements: 
		#os.system("/usr/bin/python collect_one.py " + net_element['number'] + " " + net_element['ip'])
		logging.info('\n=====collecting %s====='%(net_element['number']))
		url = "http://%s:9999/?target=%s&cmd=103"%(CDN_SERVER, net_element['number'])
		logging.info(url)
		opener = urllib2.build_opener()
		try:
			file = opener.open(url,timeout=100)
			resp = file.read()
			logging.info("resp:" + resp)
		except Exception, e:
			logging.info(e)
			
def main():
	
	logfile = '/var/log/collect.log'
	Rthandler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,backupCount=5)
	formatter = logging.Formatter('[%(asctime)s][%(levelname)s][1.01]:  %(message)s - %(filename)s:%(lineno)d')
	Rthandler.setFormatter(formatter)
	logger=logging.getLogger()
	logger.addHandler(Rthandler)
	logger.setLevel(logging.NOTSET)
    
    
	os.chdir(sys.path[0])
	while True:
		try:
			c = threading.Thread(target=routin, args=())
			c.start()
		except Exception, e:
			logging.info(e)
		time.sleep(200)
	
	
		
		
if __name__ == "__main__":
    main()
