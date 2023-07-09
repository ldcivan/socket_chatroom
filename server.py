import socket
import threading
import random
import datetime
import time
import sys
import logging


# 配置日志输出到文件
logging.basicConfig(filename='output.log', level=logging.INFO)


# 重定向 print 输出到日志
class PrintLogger:
    def write(self, message):
        logging.info(message)

sys.stdout = PrintLogger()


# 设置服务器的IP和端口号
HOST = '0.0.0.0'
PORT = 14514
clients = {}  # 存储客户端信息的字典，键为客户端编号，值为客户端套接字对象
tmp_clients = {}  # 储存正在输入密码的客户端信息


def get_time():
    curr_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
    return timestamp
 

def handle_client(conn, addr):
    while True:
        client_id = random.randint(1000, 9999) # 为客户端分配一个未使用的随机编号
        if client_id not in clients and client_id not in tmp_clients:
            break
    tmp_clients[client_id] = [conn, addr] # 将客户端信息存储到字典中
    print(f'{get_time()} {addr} is trying connect to server')
    pw_broadcast(f'*** Please type in the password of this chatroom ***', client_id)
    while True:  # 接受密码
        time.sleep(2)
        try:
            data = conn.recv(1024)
            if not data:
                continue
            password = data.decode()
            if password == "Ldc123456":  # 设置密码
                clients[client_id] = tmp_clients[client_id]
                del tmp_clients[client_id]
                break
            else:
                pw_broadcast(f'*** Wrong password ***', client_id)
                continue
        except:
            continue
    
    print(f'{get_time()} New connection from {addr}, assigned client ID: {client_id}')
    broadcast(f'\n*** User {client_id} has joined in ***\n')
    while True:  # 接受用户发文
        time.sleep(1)
        try:
            data = conn.recv(1024)
            if not data:
                break
            string = data.decode()
            if string == "#exit":
                break
            if string.startswith("#set_name#"):
                new_name = string[len("#set_name#"):]
                print(f'{get_time()} Change name: {client_id} -> {new_name}')
                if new_name in clients:  # 防止重复昵称
                    single_broadcast(f'*** {new_name} has been used! ***', client_id)
                    print(f'{get_time()} Name change failed: repeat name')
                else:
                    del clients[client_id]
                    client_id = new_name
                    clients[client_id] = [conn, addr] # 将客户端信息存储到字典中
                    single_broadcast(f'*** You have set your name: {client_id} ***', client_id)
                    print(f'{get_time()} Name changed: {new_name}')
            elif string == '#userlist':
                single_broadcast(userlist(), client_id)
            else:
                message = f'User {client_id}: {data.decode()} ({get_time()})'
                broadcast(message)
                print(message)
        except:
            break
    broadcast(f'\n*** User {client_id} has left ***\n')
    print(f'{get_time()} Connection {addr}({client_id}) closed')
    del clients[client_id] # 客户端断开连接后，从字典中删除客户端信息


def broadcast(message):
    for client_id, (conn, addr) in clients.items():
        try:
            conn.sendall(message.encode())
        except:
            del clients[client_id]
            
           
def single_broadcast(message, client_id):
    try:
        conn = clients[client_id][0]
        conn.sendall(message.encode())
    except:
        pass
    
    
def pw_broadcast(message, client_id):
    try:
        conn = tmp_clients[client_id][0]
        conn.sendall(message.encode())
    except:
        pass


def userlist():
    output = '*** User List ***\n'
    for client_id, (conn, addr) in clients.items():
        line = f"Client ID: {client_id}, Address: {addr}\n"  # 构建每行的内容
        output += line  # 将每行内容添加到输出字符串中
    return output

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f'{get_time()} Server started on {HOST}:{PORT}')
    while True:
        time.sleep(2)
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

# 关闭日志文件
logging.shutdown()
