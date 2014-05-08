#encoding:utf-8
import subprocess 
import time  
import thread  
import socket 
import os
import signal
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *

#v1 2014.2.9  解决重复起多个chrome的问题
#v2 2014.2.10 在bat文件里不需再先cd，可直接写绝对路径
#v3 2014.2.10 在背景面板显示时间
#v4 2014.5.6 在底板出现之前加载RomoteCmdExer

def kill_browser():
		print 'closing exist ones...'
		os.popen("taskkill /IM chrome.exe") 
		
def is_on_line():
		while(True):
				try:
						socket.gethostbyname("baidu.com")
						return True
				except:
						print "off line!"
						myframe.changeBgSignal.emit(2)
						kill_browser()
						time.sleep(0.5)
						continue
def start_brower():
		
		print "preparing restart browser..."
		myframe.changeBgSignal.emit(1)
		kill_browser()
		
		print 'opening a new browser...'
		pro=subprocess.Popen("C:\Program Files\Google\Chrome\Application\chrome.exe --kiosk --incognito  http://localhost/www") 
		

def check():  
	
		is_on_line()
		start_brower()
		
		s=socket.socket()
		s.bind(('',9999))
		s.listen(5)
		s.settimeout(20)

		while 1:
				try:
						cs,address = s.accept()
						print 'status:ok'
						#cs.send('hello I am server,welcome')
						#ra=cs.recv(512).strip()
						
						cs.close()
				except:
						print "timeout!"
						is_on_line()
						start_brower()
  
class myFrame(QFrame):
		changeBgSignal = pyqtSignal(int)
		
def changeBg(num):
		print "changing bg..."
		if(num==1):
			imageurl='1.jpg'
		if(num==2):
			imageurl='2.jpg'
		stylestr="background-image:url('"+imageurl+"');background-repeat: no-repeat;";	
		print "style:"+stylestr
		myframe.setStyleSheet(stylestr)

def changeTime():
		while True:
			timestr = time.strftime('%H:%M:%S',time.localtime(time.time())) 
			mylabel.setText(timestr)
			time.sleep(1)
	
def start_RomoteCmdExer():
	os.system("c:\Python27\python.exe ClientCmdExer.py")				
if __name__ == "__main__":

	os.chdir(sys.path[0])
	app = QApplication(sys.argv) 
	
	thread.start_new_thread(start_RomoteCmdExer, ()) 
	time.sleep(10)
	
	
	
	myframe = myFrame()
	
	myframe.changeBgSignal.connect(changeBg)
	myframe.changeBgSignal.emit(1)
	myframe.showFullScreen()
	
	mylabel = QLabel("                           ",myframe)
	mylabel.setStyleSheet("font-size: 68pt;color:#FFFFFF;background: transparent; border: 0px solid white;")
	mylabel.move(430, 1700)
	myframe.show()
	mylabel.show()
	
	thread.start_new_thread(check, ()) 
	thread.start_new_thread(changeTime, ())
	app.exec_()