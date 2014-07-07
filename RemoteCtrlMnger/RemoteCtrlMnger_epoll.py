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
import signal
import select
import struct

connections = {}
tasks = {}
taskid_seek=1000
terminal_reply_len=500
IMG_DIR = 'http://%s/terminal_images/'%(CDN_SERVER)
timeout=100
epoll = select.epoll()

def send_http_resp(conn,resp):
    #logging.info("resp:"+resp)
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
    #logging.info(content)
    conn.send(content)
    
def write_success_to_db(str, target):
    
    #time_sec = time.time()
    #now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_sec))+datetime.datetime.now().microsecond
    #logging.info("now:%s"%(now))
    #logging.info(str)
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
         IMG_DIR+state['snapshot_name'],\
         IMG_DIR+state['camera_img_name'])
    #print sql
    #logging.info(sql)
    try:
        mysql = Mydb(host, user, password)
        mysql.selectDb(db_name)
        mysql.query(sql)
    except Exception, e:
        logging.info(e)
    mysql.close()

def write_fail_to_db(target):
    sql = "insert into lich_ne_state (number,ping,create_time,update_time) values('%s','0',NOW(),NOW())"%(target)
    #logging.info(sql)
    try:
        mysql = Mydb(host, user, password)
        mysql.selectDb(db_name)
        mysql.query(sql)
    except Exception, e:
        logging.info(e)
    mysql.close()

def get_connection_by_fileno(fileno):
    #logging.info('looking for %d', fileno)
    for (k,v) in connections.items():
        if(connections[k]['conn'].fileno()==fileno):
            return k
    return 'unknown'
def recv_connections():
    while True:
        events = epoll.poll()
        #logging.info("got new data!")
        for fileno, event in events:
            connection=get_connection_by_fileno(fileno)
            try:
                receive = connections[connection]['conn'].recv(terminal_reply_len)
            except Exception,e:
                logging.info(e)
                epoll.unregister(connections[connection]['conn'].fileno())
                continue
            #logging.info("recv len:%d",len(receive))
            
            
            #检查接收的长度，当终端主动断开连接时，此处会收到0字节的包
            recv_len=len(receive)
            if(recv_len!=500):
                logging.info("recv err from %s,len:%d",connection,recv_len)
                epoll.unregister(connections[connection]['conn'].fileno())
                continue
            
            #开始解包
            task_id,result=struct.unpack('i496s',receive)
            result=result.strip('\x00')
            logging.info("[reply]terminal:[%s],taskid:[%d],result:[%s]",connection,task_id,result)
            
            #更新任务队列里的任务结果
            if(tasks.has_key(task_id)):
                tasks[task_id]['resp']=result
        #logging.info(tasks)
def recv_connections_iternal():
    while True:
        try:
            recv_connections()
        except Exception, e:
            logging.info(e)
def read_response(task_id):
    count=0
    while True:
        if(tasks[task_id]['resp']!='wait'):
            #
            re = tasks[task_id]['resp']
            del tasks[task_id]
            return re
        else:
            time.sleep(0.1)
            count+=1
            if(count > 360000):
                raise Exception
def get_task_id():
    global taskid_seek
    taskid_seek += 1
    if(taskid_seek >= 9999):
        taskid_seek=1000
    return taskid_seek
def send_request(task_id, cmd, target):
    
    tasks[task_id]={}
    tasks[task_id]['target']=target
    tasks[task_id]['resp']='wait'
    tasks[task_id]['time']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tasks[task_id]['cmd']=cmd
    #logging.info(tasks)
    str = struct.pack('i6s',task_id,cmd)
    
    send_len=0
    try:
        send_len=connections[target]['conn'].send(str)
    except Exception,e:
        logging.info(e)
        del tasks[task_id]
        #clear_terminal(target)
        raise Exception
        
    logging.info('[send]terminal:[%s],taskid:[%d],cmd[%s],send_len:[%d]',target,task_id,cmd,send_len)
def request_client_cmd(cmd, target):

    task_id = get_task_id()
    try:
        #re = eval(CMD_LIST['cmd']+'(connections['target'][name], connections['target']['conn'],cmd)')
        send_request(task_id, cmd, target)
        return read_response(task_id)
    except Exception, e:
        logging.info(e)
        #write_fail_to_db(target)
        return_str  = 'returncode=0&returnmsg=该终端无法连接或无响应'
        #logging.info(return_str)
        return return_str
        
def do_cmd_request(conn, r):
    data = r.split('?')[1].split(' ')[0]
    
    argu = {}
    argu[data.split('&')[0].split('=')[0]]=data.split('&')[0].split('=')[1]
    argu[data.split('&')[1].split('=')[0]]=data.split('&')[1].split('=')[1]
    
    logging.info('[cmd]%s',argu)
    
    re = request_client_cmd(argu['cmd'], argu['target'])
    logging.info('[cmd_return]%s',re)
    send_http_resp(conn,re)
    #conn.send("returncode=1&returnmsg=ok")
    
    if(argu['cmd']=='103'):
        if (re.find("returncode=1") >= 0):
            write_success_to_db(re, argu['target'])
        else:
            write_fail_to_db(argu['target'])
  
def clear_terminal(terminal_number):
    #清除terminal在服务端的所有信息
    #清除系统信息
    try:
        epoll.unregister(connections[terminal_number]['conn'].fileno())
    except:
        #当终端主动断开时，会抛异常，但这属于正常情况，所以不打日志
        #logging.info(e)
        pass
        
    try:    
        connections[terminal_number]['conn'].close()
    except:
        logging.info(e)
        
    try:
        del connections[terminal_number]
    except:
        logging.info(e)
        
    #删除taskid中的信息    
    for (k,v) in tasks.items():
        if(tasks[k]['target']==terminal_number):
            try:
                del tasks[k]
            except:
                pass
    
        
def do_login_request(conn, r):
    
    logging.info('[login]%s',r)
    
    if(r.find(',') < 0):
        conn.send("login arguments error! [%s]"%(r))
        conn.close()
        return
    
    x,terminal_number,terminal_version = r.split(',')
    
    #whether login repeatly
    
    

    #该terminal已经登陆
    if (connections.has_key(terminal_number)):
        
        #logging.info('server will quit %s',terminal_number)
        #关闭原有连接
        try:
            connections[terminal_number]['conn'].send("quit")
        except Exception, e:
            #当终端主动断开时，会抛异常，但这属于正常情况，所以不打日志
            #logging.info(e)
            pass
        clear_terminal(terminal_number)    



    #注册
    connections[terminal_number]={}
    connections[terminal_number]['conn']=conn
    connections[terminal_number]['login_time']=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    connections[terminal_number]['version']=terminal_version
    connections[terminal_number]['fileno']=conn.fileno()
    epoll.register(conn.fileno(), select.EPOLLIN)
    
    #logging.info(connections)
    
    conn.send('ok')

 
def do_online_list(conn,r):


    online_number = len(connections)
    re ='当前时间:%s\t\t在线终端数量:%d<br><hr>'%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),online_number)
    for (k,v) in connections.items():
        #客户端名称
        re += '终端:<font color=red size=4>%s</font>, 登陆时间:%s, version:%s<br> 正在执行任务:<br>'%(k,connections[k]['login_time'],connections[k]['version'])
        for mk,mv in tasks.items():
            if(tasks[mk]['target']==k):
                re += '[任务ID:%s,执行终端:%s,命令:%s,开始时间:%s,执行结果:%s] <br>'%(mk,tasks[mk]['target'],tasks[mk]['cmd'],tasks[mk]['time'],tasks[mk]['resp'])
        
        re += "<br><hr>"
        
    re += '<br><br><br><br><br>connections:%s<br>tasks:%s<br>'%(connections,tasks)

        
        
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
        #logging.info(r)
        if(r.find("cmd") >= 0):
            #logging.info("thread %s start for monitor..."%(threading.currentThread().getName()))
            do_cmd_request(conn, r)
            conn.close()
        elif(r.find("login") >= 0):
            #logging.info("thread %s start for client..."%(threading.currentThread().getName()))
            do_login_request(conn, r)
        elif(r.find("online_list") >= 0):
            #logging.info("thread %s start..."%(threading.currentThread().getName()))
            do_online_list(conn, r)
        else:
            #conn.send("sorry, I don't know you, bye!")
            conn.close()
    except:
        pass



def checker():
    heartbeat_cmd='hb'
    
    while True:
        heartbeat_task_list=[]
        for (k,v) in connections.items():
            task_id = get_task_id()
            try:
                send_request(task_id,heartbeat_cmd, k)
                heartbeat_task_list.append(task_id)
            except Exception, e:
                logging.info("%s detached!"%(k))
                clear_terminal(k)
                
            
        
        time.sleep(3)
        for task_id in heartbeat_task_list:
            if(tasks[task_id]['resp']!='on'):
                logging.info("%s detached!"%(tasks[task_id]['target']))
                clear_terminal(tasks[task_id]['target'])
            try:
                del tasks[task_id]
            except:
                pass
                        
        time.sleep(5)

def checker_iternal():
    while True:
        try:
            checker()
        except Exception, e:
            logging.info(e)
        
def init_env():
    
    #chdir
    os.chdir(sys.path[0])
    
    #init logging
    logfile = '/var/log/RomoteCtrlMnger_epoll.log'
    Rthandler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,backupCount=5)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s][1.02]:  %(message)s - %(filename)s:%(lineno)d')
    Rthandler.setFormatter(formatter)
    logger=logging.getLogger()
    logger.addHandler(Rthandler)
    logger.setLevel(logging.NOTSET)

    
        
def main():
    global timeout
    init_env()
    logging.info("starting...")
    
    
    skt=socket.socket()
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    skt.bind(('',10008))
    skt.listen(5)
    skt.settimeout(1)
    
    c = threading.Thread(target=checker_iternal, args=())
    c.start()
    
    d = threading.Thread(target=recv_connections_iternal, args=())
    d.start()
    
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
