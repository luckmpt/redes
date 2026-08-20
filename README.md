# redes

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("10.0.2.15", 8000))
s.send(b"ola")