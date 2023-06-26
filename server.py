import socket
import threading
import random

# 设置服务器的IP和端口号
HOST = '0.0.0.0'
PORT = 14514
clients = {} # 存储客户端信息的字典，键为客户端编号，值为客户端套接字对象

def handle_client(conn, addr):
    while True:
        client_id = random.randint(1000, 9999) # 为客户端分配一个随机编号
        if client_id not in clients:
            break
    clients[client_id] = conn # 将客户端信息存储到字典中
    single_broadcast(f'*** Please type in the password of this chatroom ***', client_id)
    while True:  # 接受密码
        try:
            data = conn.recv(1024)
            if not data:
                continue
            password = data.decode()
            if password == "Ldc123456":  # 设置密码
                break
            else:
                single_broadcast(f'*** Wrong password ***', client_id)
        except:
            continue
    print(f'New connection from {addr}, assigned client ID: {client_id}')
    broadcast(f'\n*** User {client_id} has joined in ***\n')
    while True:  # 接受用户发文
        try:
            data = conn.recv(1024)
            if not data:
                break
            string = data.decode()
            if string.startswith("#set_name#"):
                del clients[client_id]
                client_id = string[len("#set_name#"):]
                clients[client_id] = conn # 将客户端信息存储到字典中
                single_broadcast(f'*** You have set your name: {client_id} ***', client_id)
            else:
                message = f'User {client_id}: {data.decode()}'
                broadcast(message)
        except:
            break
    broadcast(f'\n*** User {client_id} has left ***\n')
    del clients[client_id] # 客户端断开连接后，从字典中删除客户端信息
    print(f'Connection {addr} closed')

def broadcast(message):
    for client_id, conn in clients.items():
        try:
            conn.sendall(message.encode())
        except:
            del clients[client_id]
            
def single_broadcast(message, client_id):
    try:
        conn = clients[client_id]
        conn.sendall(message.encode())
    except:
        pass

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f'Server started on {HOST}:{PORT}')
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
