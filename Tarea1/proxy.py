#PArte 1

import socket
import sys
import json

from http_utils import create_HTTP_message, parse_HTTP_message

ruta_config = sys.argv[1] if len(sys.argv) > 1 else "config.json"

with open("error.html", "rb") as archivo:
    html = archivo.read().decode("latin-1")

with open(ruta_config) as archivo:
    config = json.load(archivo)

user = config["user"]
blocked = config["blocked"]
forbidden_words = config["forbidden_words"] 


def is_blocked(target):
    if target.startswith("http://"):
        target = target[7:]
    elif target.startswith("https://"):
        target = target[8:]

    for blocked_target in blocked:
        if target == blocked_target:
            return True
        if target.startswith(blocked_target + "/"):
            return True

    return False

ip = "10.80.99.71"
puerto = 8000

# HTTP es orientado a conexion -> TCP (SOCK_STREAM)
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# evita "Address already in use" al reiniciar
# proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
proxy_socket.bind((ip, puerto))
proxy_socket.listen(3)
print(f"Escuchando en http://{ip}:{puerto}")

while True:
    # accept devuelve un socket nuevo dedicado a este cliente
    client_socket, address = proxy_socket.accept()
    # buffer grande por ahora; se achica en la Parte 2
    data = client_socket.recv(1024)
    if not data:
        client_socket.close()
        continue
    request = parse_HTTP_message(data)
    print(request["method"], request["target"])
    target = request["target"]
    if target.startswith("http://"):
        target = target[7:]
    elif target.startswith("https://"):
        target = target[8:]
    server_host = target.split("/", 1)[0]
    if is_blocked(request["target"]):
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Content-Length: "+str(len(html))+"\r\n"
            "Connection: keep-alive\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "X-ElQuePregunta: "+user+"\r\n\r\n" +
            html
        ).encode("latin-1")
        client_socket.sendall(response)
    else:
        socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Conectando a {server_host}:80")
        socket_server.connect((server_host, 80))
        socket_server.sendall(data)
        data_server = socket_server.recv(1024)
        if not data_server:
            socket_server.close()
            client_socket.close()
            continue
        response_server = parse_HTTP_message(data_server)
        body = response_server["body"]
        for word in forbidden_words:
            for forbidden, replacement in word.items():
                body = body.replace(forbidden.encode("latin-1"), replacement.encode("latin-1"))
        response_server["body"] = body
        response_server["headers"]["Content-Length"] = str(len(body))
        data_server = create_HTTP_message(response_server)
        client_socket.sendall(data_server)
        socket_server.close()
    client_socket.close()
