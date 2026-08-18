#PArte 1


import json
import socket
import sys

from http_utils import create_HTTP_message, parse_HTTP_message

HTML = "<html><body><h1>Hola</h1><p>Usuario: {user}</p></body></html>"

ruta_config = sys.argv[1] if len(sys.argv) > 1 else "config.json"
ip = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
puerto = int(sys.argv[3]) if len(sys.argv) > 3 else 8000
# python3 servidor_http.py config.json 192.168.1.176 8000

with open(ruta_config) as archivo:
    user = json.load(archivo)["user"]

# HTTP es orientado a conexion -> TCP (SOCK_STREAM)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# evita "Address already in use" al reiniciar
# server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((ip, puerto))
server_socket.listen(5)
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
    print(request["method"], request["target"])
    body = HTML.format(user=user).encode("utf-8")
    response = {
        "type": "response",
        "version": "HTTP/1.1",
        "status_code": "200",
        "reason": "OK",
        "headers": [
            ("Content-Type", "text/html; charset=utf-8"),
            # largo exacto del body en bytes, si no el navegador se cuelga
            ("Content-Length", str(len(body))),
            ("X-ElQuePregunta", user),
            ("Connection", "close"),
        ],
        "body": body,
    }
    # sendall y no send: send puede enviar solo una parte
    client_socket.sendall(create_HTTP_message(response))
    client_socket.close()