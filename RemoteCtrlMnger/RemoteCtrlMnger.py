#encoding:utf-8
import time  
import datetime
import threading
import socket 
import os
import sys
import logging
from db import *
import ast
from logging.handlers import RotatingFileHandler
from config import *
import fcntl

LOGIN_LIST = []
CMD_LIST = {}
SNAPSHOT_DIR = 'http://%s/snapshot/'%(CDN_SERVER)
CAMERA_DIR = 'http://%s/camera/'%(CDN_SERVER)

def send_http_resp(conn,resp):
    logging.info("resp:"+resp)
    header = '''HTTP/1.1 200 OK
Server: nginx/1.4.4
Date: Thu, 08 May 2014 %s GMT
Content-Type: text/html; charset=utf-8
Content-Length: %d
Last-Modified: Thu, 08 May 2014 %s GMT
Connection: keep-alive
ETag: "536b7bf9-4"
Accept-Ranges: bytes

'''%(datetime.datetime.now().strftime('%H:%M:%S'),len(resp),datetime.datetime.now().strftime('%H:%M:%S'))

    
    content = header + resp + '\n'
    logging.info(content)
    conn.send(content)
    
def write_success_to_db(str, target):
    
    #time_sec = time.time()
    #now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_sec))+datetime.datetime.now().microsecond
    #logging.info("now:%s"%(now))
    logging.info(str)
    state = ast.literal_eval(str.split('returnmsg=')[1])
    sql="insert into lich_ne_state \
        (number,os,version,cpu_utility,available_mem,available_disk,temperature,air_condition_state,bandwidth,ping,ap_state,create_time,update_time,snapshot_name,camera_img_name) \
        values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',NOW(),NOW(),'%s','%s')" % \
        (target, \
         state['os'], \
         state['version'], \
         state['cpu_utility'], \
         state['available_mem'], \
         state['available_disk'],\
         state['temperature'],\
         state['air_condition_state'],\
         state['bandwidth'],\
         state['ping'],\
         state['ap_state'],\
         SNAPSHOT_DIR+state['snapshot_name'],\
         SNAPSHOT_DIR+state['camera_img_name'])
    #print sql
    logging.info(sql)
    try:
        mysql = Mydb(host, user, password)
        mysql.selectDb(db_name)
        mysql.query(sql)
    except Exception, e:
        logging.info(e)
    mysql.close()

def write_fail_to_db(target):
    sql = "insert into lich_ne_state (number,ping,create_time,update_time) values('%s','0',NOW(),NOW())"%(target);
    logging.info(sql)
    try:
        mysql = Mydb(host, user, password)
        mysql.selectDb(db_name)
        mysql.query(sql)
    except Exception, e:
        logging.info(e)
    mysql.close()
        
def cmd_101(target, conn, cmd):
    conn.send(cmd)
    return conn.recv(512)

def cmd_102(target, conn, cmd):
    conn.send(cmd)
    return conn.recv(512)

def cmd_103(target, conn, cmd):#collet_client_state
    try:
       
        conn.send(cmd)
        re = conn.recv(512)
        
        #write db when success
        if (re.find("returncode=1") >= 0):
            write_success_to_db(re, target)
            
        return re 
    
    except Exception, e:
        logging.info(e)
        write_fail_to_db(target)
        return 'returncode=0&returnmsg=%s'%(e)


def cmd_104(target, conn, cmd):
    conn.send(cmd)
    return conn.recv(512)

def cmd_105(target, conn, cmd):
    conn.send(cmd)
    return conn.recv(512)

def cmd_106(target, conn, cmd):
    conn.send(cmd)
    return conn.recv(512)

def cmd_107(target, conn, cmd):
    conn.send(cmd)
    return conn.recv(512)
    
def cmd_108(target, conn, cmd):  
    conn.send(cmd)
    return conn.recv(512)

    
def request_client_cmd(cmd, target):
    global LOGIN_LIST
    global CMD_LIST
    #logging.info(LOGIN_LIST)
    logging.info("target:%s"%(target))
    
    if(CMD_LIST.has_key(cmd) == False):
        return_str = 'returncode=0&returnmsg=命令不存在'
        logging.info(return_str)
        return return_str
                
    for index in range(len(LOGIN_LIST)):
        try:
            if(LOGIN_LIST[index][0].lower() == target.lower()):
                if ((LOGIN_LIST[index][2] == 1) and (cmd != '106')):
                    return "returncode=0&returnmsg=系统繁忙，请稍后再试"
                #logging.info("sending cmd %s to target %s", cmd,target)
                #logging.info("ex...index:%d,%s"%(index, LOGIN_LIST[index][1]))
                #fcntl.flock(LOGIN_LIST[index][1], fcntl.LOCK_EX|fcntl.LOCK_NB)
                logging.info("flag:%d",LOGIN_LIST[index][2])
                LOGIN_LIST[index][2] = 1
                try:
                    re = eval(CMD_LIST[cmd]+'(LOGIN_LIST[index][0], LOGIN_LIST[index][1],cmd)')
                except Exception, e:
                    logging.info(e)
                    return 'returncode=0&returnmsg=%s'%(e)
                LOGIN_LIST[index][2] = 0
                #fcntl.flock(LOGIN_LIST[index][1], fcntl.LOCK_UN)  
                return re
        except Exception, e:
            logging.info(e)
            return_str = 'returncode=0&returnmsg=该终端无法连接'
           #logging.info(return_str)
            return return_str

    write_fail_to_db(target)
    return_str  = 'returncode=0&returnmsg=该终端无法连接'
    logging.info(return_str)
    return return_str
        
def do_HTTP_request(conn, r):
    data = r.split('?')[1].split(' ')[0]
    
    argu = {}
    argu[data.split('&')[0].split('=')[0]]=data.split('&')[0].split('=')[1]
    argu[data.split('&')[1].split('=')[0]]=data.split('&')[1].split('=')[1]
    
    logging.info(argu)
    re = request_client_cmd(argu['cmd'], argu['target'])
    logging.info(re)
    send_http_resp(conn,re)
    #conn.send("returncode=1&returnmsg=ok")
  
    
def do_login_request(conn, r):
    
    logging.info(r)
    
    if(r.find(',') < 0):
        conn.send("login arguments error! [%s]"%(r))
        conn.close()
        return
    
    terminal_number = r.split(',')[1]
    
    #whether login repeatly
    
    
    for index in range(len(LOGIN_LIST)):
        if (LOGIN_LIST[index][0] == terminal_number):
            LOGIN_LIST[index][1].send("quit")
            LOGIN_LIST[index][1]=conn
            del LOGIN_LIST[index]
            break
            
    
    #
    LOGIN_LIST.append([terminal_number, conn,0])
    #logging.info(LOGIN_LIST)
    conn.send("ok")
 
def do_online_list(conn,r):
    global LOGIN_LIST
    logging.info(LOGIN_LIST)
    online_number = len(LOGIN_LIST)
    re ='%d\n'%(online_number)
    for index in range(online_number):
        #conn.send('%s,%d\n'%(LOGIN_LIST[index][0],LOGIN_LIST[index][2]))
        re += '%s,%d\n'%(LOGIN_LIST[index][0],LOGIN_LIST[index][2])
    send_http_resp(conn,re)

def do_online_number(conn,r):
    online_number = len(LOGIN_LIST)
    re = 'returncode=1&returnmsg=%d'%(online_number);
    
    send_http_resp(conn,re)
  
def worker(no,conn):
    #logging.info("thread %s start..."%(threading.currentThread().getName()))
    
    '''
    l_onoff = 1                                                                                                                                                           
    l_linger = 0                                                                                                                                                          
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', l_onoff, l_linger))
    '''
    try:
        r = conn.recv(512)
        logging.info(r)
        if(r.find("cmd") >= 0):
            logging.info("thread %s start for monitor..."%(threading.currentThread().getName()))
            do_HTTP_request(conn, r)
            conn.close()
        elif(r.find("login") >= 0):
            logging.info("thread %s start for client..."%(threading.currentThread().getName()))
            do_login_request(conn, r)
        elif(r.find("online_list") >= 0):
            logging.info("thread %s start..."%(threading.currentThread().getName()))
            do_online_list(conn, r)
        elif(r.find("online_number") >= 0):
            do_online_number(conn, r)
        else:
            #conn.send("sorry, I don't know you, bye!")
            conn.close()
    except:
        pass
    
def checker():
    global LOGIN_LIST
    while True:
        del_flag = 0
        for index in range(len(LOGIN_LIST)):
            try:
                LOGIN_LIST[index][1].send("heartbeat")
            except:
                del LOGIN_LIST[index]
                del_flag = 1
                break
        
        if(del_flag == 0):
            #logging.info(len(LOGIN_LIST))
            time.sleep(10)


def init_env():
    
    #chdir
    os.chdir(sys.path[0])
    
    #init logging
    logfile = '/var/log/RomoteCtrlMnger.log'
    Rthandler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,backupCount=5)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s][1.01]:  %(message)s - %(filename)s:%(lineno)d')
    Rthandler.setFormatter(formatter)
    logger=logging.getLogger()
    logger.addHandler(Rthandler)
    logger.setLevel(logging.NOTSET)
    
    global CMD_LIST
    CMD_LIST['101'] =  'cmd_101'
    CMD_LIST['102'] =  'cmd_102'
    CMD_LIST['103'] =  'cmd_103'
    CMD_LIST['104'] =  'cmd_104'
    CMD_LIST['105'] =  'cmd_105'
    CMD_LIST['106'] =  'cmd_106'
    CMD_LIST['107'] =  'cmd_107'
    CMD_LIST['108'] =  'cmd_108'

    
        
def main():
    
    init_env()
    logging.info("starting...")
    
    
    skt=socket.socket()
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    skt.bind(('',9999))
    skt.listen(5)
    skt.settimeout(40)
    
    c = threading.Thread(target=checker, args=())
    c.start()
    
    while 1:
        try:
            conn,address = skt.accept()
            #thread.start_new_thread(worker,(1,conn))
            t= threading.Thread(target=worker, args=(1,conn))
            t.start()

        except Exception, e:
            #logging.info(e)
            pass
            
if __name__ == "__main__":
    main()