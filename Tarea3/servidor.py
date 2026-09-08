import socket

socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind(("localhost", 8000))
while True:
    data = ""
    while data[-15:] != b'FIN DEL ARCHIVO':
        msg, addr = socket.recvfrom(16)
        if not data:
            break
        data += msg
    print(data)