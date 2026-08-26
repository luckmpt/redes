import socket
from dnslib import DNSRecord

server_address = ("10.172.47.71", 8000)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # socket no orientado a conexion, anotar en informe
sock.bind(server_address)
while True:
        data, address = sock.recvfrom(4096)
        print(data)
