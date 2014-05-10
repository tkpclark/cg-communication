#encoding:utf-8
import socket
import time
import os
import sys
import psutil
import platform
import ImageGrab
from ftplib import FTP
import subprocess
import urllib
from config import *
import threading
import re



#function of Get CPU State  

cmd = {}


def ftp_up(filename): 
    ftp=FTP()
    ftp.set_debuglevel(2)
    ftp.connect(ftp_server,ftp_port)
    ftp.login(ftp_username,ftp_password)
    #print ftp.getwelcome()
    ftp.cwd(ftp_upload_path)
    bufsize = 1024
    file_handler = open(filename,'rb')
    ftp.storbinary('STOR %s' % os.path.basename(filename),file_handler,bufsize)
    ftp.set_debuglevel(0) 
    file_handler.close() 
    ftp.quit() 
    #print "ftp up OK" 

#===============
def get_cpu_utility():  
    return (str(round(psutil.cpu_percent()/100,2)))  
    
#function of Get Memory  
def get_available_mem():  
    return round((1 - psutil.phymem_usage().percent/100),2)
  
def get_available_disk():
	return int(psutil.disk_usage('c:')[2]/(1024*1024*1024))

def get_version():
    return "0.01"

def get_os():
    return platform.platform()

def get_ap_state():
    return "1"

def get_temperature():
    return "60"

def get_air_condition_state():
    return "1"

def get_ping():
	r = os.popen("ping -n 1 %s"%(server_ip))  
	result = r.read()
	s = re.search(r"[<=]\d+ms",result)
	s = re.search(r"\d+",s.group())
	#print result
	r.close() 
	return s.group()

def get_bandwidth():
	tmp_file = 'file.tmp.%s'%(time.time())
	t1 = time.time()
	urllib.urlretrieve(bandwidth_url, tmp_file)
	t2 = time.time()
	period = t2 - t1
	
	bandwidth = int(os.path.getsize(tmp_file)/period/1000)
	#print os.path.getsize(tmp_file)
	time.sleep(0.1)
	#os.system("rm %s -f"%(tmp_file))
	os.system("del %s -f"%(tmp_file))
	return '%dK/s'%(bandwidth)
	
def get_snapshot():
	
	global terminal_number
	img = ImageGrab.grab()
	filename = '%s.%s.jpg'%(terminal_number, time.time())
	img.save(filename)
	ftp_up(filename)
	os.system('del %s'%(filename))
	
	
	return filename

def get_camera_img():
	pass
#===============
def cmd_101():
	return 'returncode=1&returnmsg=ok'	
	
def cmd_102():
	os.system('c:\www\\rsync.exe -vzrtopgu --progress --delete root@115.28.134.72::www /cygdrive/C/www/lsh --password-file=/cygdrive/C/www/rsync.pass')
	os.system('c:\www\\rsync.exe -vzrtopgu --progress --delete root@115.28.134.72::uploadfile /cygdrive/C/www/uploadfile --password-file=/cygdrive/C/www/rsync.pass')
	os.system('c:\www\\rsync.exe -vzrtopgu --progress --delete root@115.28.134.72::include /cygdrive/C/www/include --password-file=/cygdrive/C/www/rsync.pass')
	return 'returncode=1&returnmsg=ok'


	
def cmd_103():
	
	status_info = {}
    
	status_info['available_mem'] = get_available_mem()
	status_info['os'] = get_os()
	status_info['cpu_utility'] = get_cpu_utility()
	status_info['available_disk'] = get_available_disk()
	status_info['version'] = get_version()
	status_info['ap_state'] = get_ap_state()
	status_info['temperature'] = get_temperature()
	status_info['air_condition_state'] = get_air_condition_state()
	status_info['ping'] = get_ping()
	status_info['bandwidth'] = get_bandwidth()
	status_info['snapshot_name'] = get_snapshot()
	status_info['camera_img_name'] = get_snapshot()
	
	return 'returncode=1&returnmsg=%s'%(status_info)

def cmd_104():
	return 'returncode=1&returnmsg=ok'

def cmd_105():
	os.system("taskkill /IM chrome.exe") 
	return 'returncode=1&returnmsg=ok'

def cmd_106():
	os.system("shutdown -f -r -t 0")
	return 'returncode=1&returnmsg=ok'

def cmd_107():
	os.system("shutdown -f -s -t 0")
	return 'returncode=1&returnmsg=ok'
	
def cmd_108():
	global version
	return 'returncode=1&returnmsg=%s'%(version)

def handler(data,sock):
	print 'workder'
	try:
		re = eval(cmd[data]+"()")
		print re
		print 'sendlen:%d'%(sock.send(re))
	except Exception, e:
		print e
		sock.send('returncode=0&returnmsg=内部错误:[%s]'%(e))
	
def main():
   
	cmd['101'] = 'cmd_101';
	cmd['102'] = 'cmd_102';
	cmd['103'] = 'cmd_103';
	cmd['104'] = 'cmd_104';
	cmd['105'] = 'cmd_105';
	cmd['106'] = 'cmd_106';
	cmd['107'] = 'cmd_107';
	cmd['108'] = 'cmd_108';


	while True:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
		sock.settimeout(30)
		try:
			print 'connecting %s...'%(server_ip)
			sock.connect((server_ip, server_port))  
			sock.send('login,%s'%(terminal_number))
			data = sock.recv(32)
			print data
			if(data != 'ok'):
				raise Exception
				
		  	while True:
		  		try:
					data = sock.recv(1024) 
					print 'Received: ', data
					if(data == ''):
						print 'recv null'
						break
					#print cmd
					
					
						
					if(data == 'quit'):
						print 'your number is logging somewhere else'
						time.sleep(3)
						sys.exit(0)
						
					if(data == 'heartbeat'):
						sock.send('on')
						continue
						
					if(cmd.has_key(data)):
						t= threading.Thread(target=handler, args=(data,sock))
						t.start()
						#handler(data,sock)
						
				except Exception, e:
					print e
					raise Exception
		except Exception, e:
			print e
			print 'close connection'
			sock.close()
		time.sleep(1)
		
if __name__ == "__main__":
    os.chdir(sys.path[0])
    main()