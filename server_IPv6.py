import socket

# HOST = "192.168.132.252"  # server IP
HOST = "fe80::2ff2:6d10:708:ad8d"  # server IPv6
PORT = 8000  # Port to listen on (non-privileged ports are > 1023)
addrinfo = socket.getaddrinfo(HOST, PORT, socket.AF_INET6, socket.SOCK_STREAM)
print(addrinfo)
(family, socktype, proto, canonname, sockaddr) = addrinfo[0]

with socket.socket(family, socktype, proto) as s:
    s.bind(sockaddr)
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            conn.sendall(bytes(input(), 'utf-8'))