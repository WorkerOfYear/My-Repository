import socket

sock = socket.socket()
sock.connect(('localhost', 9090))
mess = 'hello, world!'
massage = mess.encode()
sock.send(massage)

data = sock.recv(1024)
sock.close()

print(data)
