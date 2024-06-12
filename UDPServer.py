from socket import *

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(("", serverPort))

print("Server is ready")

while True:
    _, clientAdd = serverSocket.recvfrom(2048)
    message = input()
    serverSocket.sendto(str(message).encode('utf-8'), clientAdd)