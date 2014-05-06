kill -9 `ps ax -H|grep RemoteCtrlMnger|grep -v grep|awk '{print $1}'`
