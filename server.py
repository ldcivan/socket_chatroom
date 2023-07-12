import socket
import threading
import random
import json
import datetime
import time
import sys
import logging

# 配置日志输出到文件
logging.basicConfig(filename='output.log', level=logging.INFO)
logging.basicConfig(filename='output.log', level=logging.ERROR)


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
timeout = 5  # socket连接超时时间


def get_time():
    curr_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
    return timestamp


def handle_client(conn, addr):
    while True:
        client_id = str(random.randint(1000, 9999))  # 为客户端分配一个未使用的随机编号
        if client_id not in clients and client_id not in tmp_clients:
            break
    tmp_clients[client_id] = [conn, addr]  # 将客户端信息存储到字典中
    print(f'{get_time()} {addr} is trying connect to server')
    pw_broadcast(f'*** Please type in the password of this chatroom ***', client_id)
    while True:  # 接受密码
        time.sleep(2)
        try:
            # 接收数据直到遇到换行符
            header = b''
            if b'\r\n' not in header:
                header += conn.recv(1024)
                if header == b'':
                    continue
            # 解析标头，获取图片数据长度
            content_length = int(header.split(b'|')[0])
            datatype = header.split(b'|')[1].split(b'\r\n')[0].decode()
            # 接收主体数据
            data = b''
            if b'<STREAMEND>' not in data:
                data += conn.recv(content_length)
            if not data:
                continue
            password = data.decode().rstrip('<STREAMEND>')
            if password == "Ldc123456":  # 设置密码
                clients[client_id] = tmp_clients[client_id]
                del tmp_clients[client_id]
                break
            else:
                pw_broadcast(f'*** Wrong password ***', client_id)
                continue
        except Exception as e:
            # 记录错误日志
            logging.error(str(e), 'position 0')
            continue

    print(f'{get_time()} New connection from {addr}, assigned client ID: {client_id}')
    broadcast(f'\n*** User {client_id} has joined in ***\n')
    while True:  # 接受用户发文
        time.sleep(1)
        try:
            # 接收数据直到遇到换行符
            header = b''
            if b'\r\n' not in header:
                header += conn.recv(1024)
                if header == b'':
                    continue
            # 解析标头，获取图片数据长度
            content_length = int(header.split(b'|')[0])
            datatype = header.split(b'|')[1].split(b'\r\n')[0].decode()
            # 接收主体数据
            data = b''
            while b'<STREAMEND>' not in data:
                data += conn.recv(content_length)

            if not data:
                break
            if datatype != "text":
                broadcast(data.rstrip(b'<STREAMEND>'))
                print(f'User {client_id} send an image({content_length}) ({get_time()})')
            else:
                string = data.decode().rstrip('<STREAMEND>')
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
                        clients[client_id] = [conn, addr]  # 将客户端信息存储到字典中
                        single_broadcast(f'*** You have set your name: {client_id} ***', client_id)
                        print(f'{get_time()} Name changed: {new_name}')
                elif string == '#userlist':
                    single_broadcast(userlist(client_id), client_id)
                elif string == '#msg_history':
                    single_broadcast(msg_history(), client_id)
                elif string.startswith("#whisper#"):
                    target_client_id, message = split_whisper(string)
                    if target_client_id in clients:
                        single_broadcast(f'You whisper to user {target_client_id}: {message} ({get_time()})', client_id)
                        single_broadcast(f'User {client_id} whisper to you: {message} ({get_time()})', target_client_id)
                        print(f'User {client_id} whisper to user {target_client_id}: {message} ({get_time()})')
                    else:
                        single_broadcast(f'*** User not found ***', client_id)
                else:
                    message = f'User {client_id}: {data.decode()} ({get_time()})'
                    broadcast(message)
                    print(message)
        except Exception as e:
            # 记录错误日志
            logging.error(str(e), 'position 1')
            continue
    broadcast(f'\n*** User {client_id} has left ***\n')
    print(f'{get_time()} Connection {addr}({client_id}) closed')
    del clients[client_id]  # 客户端断开连接后，从字典中删除客户端信息


def broadcast(message):
    for client_id, (conn, addr) in list(clients.items()):
        try:
            if isinstance(message, bytes):
                # 构造自定义标头
                header = f"{len(message)}|image\r\n".ljust(1024)
                # 发送标头和图片数据
                conn.sendall(header.encode('utf-8') + message + b'<STREAMEND>')
            else:
                # 构造自定义标头
                header = f"{len(message)}|text\r\n".ljust(1024)
                # 发送标头和图片数据
                conn.sendall(header.encode('utf-8') + message.encode('utf-8') + b'<STREAMEND>')
        except Exception as e:
            # 记录错误日志
            logging.error(str(e), 'position 2')
            del clients[client_id]
    if not isinstance(message, bytes):
        msg_recorder(message)


def single_broadcast(message, client_id):
    try:
        conn = clients[client_id][0]
        if isinstance(message, bytes):
            # 构造自定义标头
            header = f"{len(message)}|image\r\n".ljust(1024)
            # 发送标头和图片数据
            conn.sendall(header.encode('utf-8') + message)
        else:
            # 构造自定义标头
            header = f"{len(message)}|text\r\n".ljust(1024)
            # 发送标头和图片数据
            conn.sendall(header.encode('utf-8') + message.encode('utf-8') + b'<STREAMEND>')
    except Exception as e:
        # 记录错误日志
        logging.error(str(e), 'position 3')
        pass


def pw_broadcast(message, client_id):
    try:
        conn = tmp_clients[client_id][0]
        # 构造自定义标头
        header = f"{len(message)}|text\r\n".ljust(1024)
        # 发送标头和图片数据
        conn.sendall(header.encode('utf-8') + message.encode('utf-8') + b'<STREAMEND>')
    except Exception as e:
        # 记录错误日志
        logging.error(str(e), 'position 4')
        pass


def userlist(req_client):
    output = '*** User List ***\n'
    for client_id, (conn, addr) in list(clients.items()):
        if req_client != client_id:
            line = f"Client ID: {client_id}, Address: {addr}\n"  # 构建每行的内容
        else:
            line = f"Client ID: {client_id}, Address: {addr} (You)\n"  # 构建每行的内容
        output += line  # 将每行内容添加到输出字符串中
    return output


def msg_recorder(message):
    max_messages = 10  # 最大消息数量
    file_path = 'messages.json'  # JSON 文件路径

    # 读取现有的消息列表
    try:
        with open(file_path, 'r') as file:
            messages = json.load(file)
    except FileNotFoundError:
        messages = []

    # 添加新消息到列表末尾
    messages.append(message)

    # 如果消息数量超过最大值，删除第一条消息
    if len(messages) > max_messages:
        messages = messages[1:]

    # 保存消息列表到 JSON 文件
    with open(file_path, 'w') as file:
        json.dump(messages, file)


def msg_history():
    output = '*** Message history start ***\n'
    # 读取 JSON 文件
    file_path = 'messages.json'  # JSON 文件路径
    with open(file_path, 'r') as file:
        data = json.load(file)
    # 打印所有值
    for msg in data:
        output += f'{msg}\n'
    output += '*** Message history end ***'
    return output


def split_whisper(string):
    parts = string.split('#')
    client_id = parts[2]
    message = parts[3]
    return client_id, message


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
