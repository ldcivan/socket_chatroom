import socket
import threading
import logging
import base64
from PIL import Image
from io import BytesIO
import time


# 配置日志记录器
logging.basicConfig(filename='error.log', level=logging.ERROR)

print(
'''
This is a note tell you how to use the program
0. Type in the password if needed, and you can ask admin to get the password
1. Type in some word then press Enter to send message
2. Send "#set_name#" + {your nickname} to change the random id to a certain nickname
3. Send "#userlist" to get user list and their IP, and send "#whisper#" + {target_username} + "#" + {your_msg}
4. Send "#msg_history" to get 10 message history
5. Send "#exit" to close the client
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
            time.sleep(1)
            # 接收数据直到遇到换行符
            header = b''
            if b'\r\n' not in header:
                header += client.recv(1024)
            # 解析标头，获取图片数据长度
            content_length = int(header.split(b'|')[0])
            datatype = header.split(b'|')[1].split(b'\r\n')[0].decode()
            # 接收主体数据
            data = b''
            while b'<STREAMEND>' not in data:
                data += client.recv(content_length)

            if data:
                # 解码头部和图片数据
                if datatype != "text":
                    # Base64 编码字符串
                    base64_str = data.rstrip(b'<STREAMEND>').decode('utf-8')

                    # 将 Base64 编码字符串转换为二进制数据
                    image_data = base64.b64decode(base64_str)

                    # 创建 BytesIO 对象
                    image_stream = BytesIO(image_data)

                    # 打开并保存图像
                    image = Image.open(image_stream)
                    image.save("image.jpg")  # 将图像保存为 JPEG 格式
                else:
                    message = data.decode('utf-8').rstrip('<STREAMEND>')
                    print(message)
        except Exception as e:
            logging.error(str(e), 'position 0')
            # 如果出现异常，则关闭客户端连接
            try:
                client.send('#exit'.encode('utf-8'))
                client.close()
            except:
                break

# 创建一个新的线程来接收服务器的消息
receive_thread = threading.Thread(target=receive_message)
receive_thread.start()

# 循环来发送消息
while True:
    try:
        # 输入消息
        message = input()

        if message == '#exit':
            header = f"{len(message.encode('utf-8'))}|text\r\n".ljust(1024)
            client.send(header.encode('utf-8') + message.encode('utf-8') + b'<STREAMEND>')
            # 如果输入内容为#exit，则关闭客户端连接
            client.close()
            break

        #elif message == '#send_img':
        #    image_path = input('Please type in the path to img: ')
        #    # 读取图片数据
        #    with open(image_path, 'rb') as file:
        #        image_data = file.read()
        #    # 将二进制数据转换为 Base64 编码
        #    base64_data = base64.b64encode(image_data)
        #    base64_str = base64_data.decode('utf-8')
        #    # 构造自定义标头
        #    header = f"{len(image_data)}|image\r\n".ljust(1024)
        #    # 发送标头和图片数据
        #    client.sendall(header.encode('utf-8') + base64_str.encode('utf-8') + b'<STREAMEND>')
        #    print(len(image_data), 'send image')
        #    print(image_data)
        else:
            # 发送消息给服务器
            header = f"{len(message.encode('utf-8'))}|text\r\n".ljust(1024)
            client.send(header.encode('utf-8') + message.encode('utf-8') + b'<STREAMEND>')
    except Exception as e:
        logging.error(str(e), 'position 1')
        # 如果出现异常，则关闭客户端连接
        try:
            client.send('#exit'.encode('utf-8'))
            client.close()
        except:
            pass
        break


print('Client closed!')
# 关闭日志文件
logging.shutdown()
