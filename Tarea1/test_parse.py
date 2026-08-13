"""Test: parsear y reconstruir debe devolver el mensaje identico."""

from http_utils import create_HTTP_message, parse_HTTP_message

# request real capturada desde el navegador en el paso 1
original = b'GET / HTTP/1.1\r\nHost: 127.0.0.1:8000\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\n\r\n'
# la convertimos a diccionario y de vuelta a bytes
assert create_HTTP_message(parse_HTTP_message(original)) == original
print("funciona")