import socket
import threading

print(
'''
This is a note tell you how to use the program
1. Type in some word then press Enter to send message
2. Send "#set-name#" + {your nickname} to change the random id to a certain nickname
3. Send "#exit" to close the client
'''
)

# 设置服务器的IP和端口号
HOST = '123.57.134.53'
PORT = 14514

# 创建一个套接字对象
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 连接服务器
client.connect((HOST, PORT))

# 定义一个函数来接收服务器的消息
def receive_message():
    while True:
        try:
            # 接收服务器的消息
            message = client.recv(1024).decode('utf-8')
            if message:
                print(message)
        except:
            # 如果出现异常，则关闭客户端连接
            client.close()
            break

# 创建一个新的线程来接收服务器的消息
receive_thread = threading.Thread(target=receive_message)
receive_thread.start()

# 循环来发送消息
while True:
    # 输入消息
    message = input()

    if message == '#exit':
        # 如果输入内容为#exit，则关闭客户端连接
        client.close()
        break

    # 发送消息给服务器
    client.send(message.encode('utf-8'))

print('Client closed!')
