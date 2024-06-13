import socket
import time

HOST = "192.168.137.1"  # server IP
PORT = 8000  # Port to listen on (non-privileged ports are > 1023)

count = 0
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            conn.send(bytes(input(), 'utf-8'))


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try {

}