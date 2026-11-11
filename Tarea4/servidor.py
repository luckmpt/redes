# Uso: python3 servidor.py <ip> <puerto> [--gbn] [--debug] [--perdida p] [--timeout t]
import sys

from SocketTCP import SocketTCP

address = (sys.argv[1], int(sys.argv[2]))
SocketTCP.debug = "--debug" in sys.argv
if "--perdida" in sys.argv:
    SocketTCP.perdida = float(sys.argv[sys.argv.index("--perdida") + 1])
if "--timeout" in sys.argv:
    SocketTCP.timeout = float(sys.argv[sys.argv.index("--timeout") + 1])
mode = "go_back_n" if "--gbn" in sys.argv else "stop_and_wait"

server_socketTCP = SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()
full_message = connection_socketTCP.recv(10 ** 9, mode=mode)
sys.stdout.buffer.write(full_message)
sys.stdout.flush()
connection_socketTCP.recv_close()
