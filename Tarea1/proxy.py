"""Parte 2: proxy HTTP que bloquea dominios y censura palabras.

Uso: python3 proxy.py [config.json] [ip] [puerto] [buff_size]
"""

import json
import socket
import sys

from http_utils import create_HTTP_message, del_header, recv_HTTP_message

ruta_config = sys.argv[1] if len(sys.argv) > 1 else "config.json"
ip = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
puerto = int(sys.argv[3]) if len(sys.argv) > 3 else 8000
buff_size = int(sys.argv[4]) if len(sys.argv) > 4 else 1024

with open(ruta_config) as archivo:
    config = json.load(archivo)

user = config["user"]
blocked = config["blocked"]
forbidden_words = config["forbidden_words"]

with open("error.html", "rb") as archivo:
    html_403 = archivo.read()

with open("403.jpeg", "rb") as archivo:
    imagen_403 = archivo.read()


def separar_target(target):
    """Del target de la request saca (host, puerto, ruta)."""
    if target.startswith("http://"):
        target = target[7:]
    host, _, ruta = target.partition("/")
    ruta = "/" + ruta
    # el host puede venir como "dominio:puerto"
    if ":" in host:
        host, _, p = host.partition(":")
        return host, int(p), ruta
    return host, 80, ruta


def esta_bloqueado(host, ruta):
    """True si el destino aparece en la lista blocked del config."""
    for prohibido in blocked:
        if host == prohibido or (host + ruta).startswith(prohibido):
            return True
    return False


def armar_respuesta(status, reason, tipo, cuerpo):
    """Arma una respuesta HTTP propia del proxy (403 o imagen)."""
    return {
        "type": "response",
        "version": "HTTP/1.1",
        "status_code": status,
        "reason": reason,
        "headers": {
            "Content-Type": tipo,
            "Content-Length": str(len(cuerpo)),
            "X-ElQuePregunta": user,
            "Connection": "close",
        },
        "body": cuerpo,
    }


def censurar(body):
    """Reemplaza las palabras prohibidas dentro del body."""
    for par in forbidden_words:
        for palabra, reemplazo in par.items():
            body = body.replace(palabra.encode("latin-1"), reemplazo.encode("latin-1"))
    return body


proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
proxy_socket.bind((ip, puerto))
proxy_socket.listen(5)
print(f"Proxy escuchando en {ip}:{puerto} (buff_size={buff_size})")

while True:
    client_socket, address = proxy_socket.accept()
    try:
        request = recv_HTTP_message(client_socket, buff_size)
        if request is None:
            continue
        host, puerto_destino, ruta = separar_target(request["target"])
        print(request["method"], host, ruta)

        if ruta.endswith("/403.jpeg"):
            # la imagen del 403 la sirve el proxy desde el disco
            respuesta = armar_respuesta("200", "OK", "image/jpeg", imagen_403)
            client_socket.sendall(create_HTTP_message(respuesta))

        elif esta_bloqueado(host, ruta):
            respuesta = armar_respuesta("403", "Forbidden", "text/html; charset=utf-8", html_403)
            client_socket.sendall(create_HTTP_message(respuesta))

        else:
            # el servidor final espera la ruta sola, no la URL completa
            request["target"] = ruta
            request["headers"]["X-ElQuePregunta"] = user
            request["headers"]["Connection"] = "close"
            # sin gzip, si no el body viene comprimido y no se puede censurar
            request["headers"]["Accept-Encoding"] = "identity"
            del_header(request, "Proxy-Connection")

            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((host, puerto_destino))
            server_socket.sendall(create_HTTP_message(request))
            # a un HEAD el servidor responde sin body
            respuesta = recv_HTTP_message(server_socket, buff_size, request["method"] != "HEAD")
            server_socket.close()

            if respuesta is not None:
                respuesta["body"] = censurar(respuesta["body"])
                # el largo cambia al censurar, hay que recalcularlo
                respuesta["headers"]["Content-Length"] = str(len(respuesta["body"]))
                respuesta["headers"]["Connection"] = "close"
                client_socket.sendall(create_HTTP_message(respuesta))
    except Exception as error:
        print("error:", error)
    finally:
        client_socket.close()
