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
import string

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

def rsync(n, number):
	url = "http://%s:9999/?target=%s&cmd=102"%(CDN_SERVER, number)
	logging.info(url)
	opener = urllib2.build_opener()
	try:
		file = opener.open(url,timeout=100)
		resp = file.read()
		logging.info(number + " resp:" + resp)
	except Exception, e:
		logging.info(e)
		
def routin():
	net_elements = get_net_element()
	for net_element in net_elements: 
		#os.system("/usr/bin/python collect_one.py " + net_element['number'] + " " + net_element['ip'])
		t= threading.Thread(target=rsync, args=(1,net_element['number']))
		t.start()

def routin_sleep():
	sql = "select html_rsync_interval from lich_system_config"
	try:
		mysql = Mydb(host, user, password)
		mysql.selectDb(db_name)
		#logging.info(sql)
		re = mysql.queryAll(sql)
		#logging.info(re)
	except Exception, e:
		logging.info(e)
	mysql.close()
	time.sleep(string.atoi(re[0]['html_rsync_interval']))
		
def main():
	
	logfile = '/var/log/rsync.log'
	Rthandler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,backupCount=5)
	formatter = logging.Formatter('[%(asctime)s][%(levelname)s][1.01]:  %(message)s - %(filename)s:%(lineno)d')
	Rthandler.setFormatter(formatter)
	logger=logging.getLogger()
	logger.addHandler(Rthandler)
	logger.setLevel(logging.NOTSET)
    
    
	os.chdir(sys.path[0])
	while True:
		try:
			routin()
		except Exception, e:
			logging.info(e)
		routin_sleep()
	
	
		
		
if __name__ == "__main__":
    main()
