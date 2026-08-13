#PArte 1


import json
import socket
import sys

from http_utils import create_HTTP_message, parse_HTTP_message

ip = "10.0.2.15"
puerto = 8000


# HTTP es orientado a conexion -> TCP (SOCK_STREAM)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# evita "Address already in use" al reiniciar
# server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((ip, puerto))
server_socket.listen(3)
print(f"Escuchando en http://{ip}:{puerto}")

while True:
    # accept devuelve un socket nuevo dedicado a este cliente
    client_socket, address = server_socket.accept()
    # buffer grande por ahora; se achica en la Parte 2
    data = client_socket.recv(1024)
    if not data:
        client_socket.close()
        continue
    request = parse_HTTP_message(data)
    print(request)
    client_socket.close()