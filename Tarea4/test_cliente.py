# Uso: python3 test_cliente.py <ip> <puerto> [--gbn] [--cc] [--debug] [--perdida p] [--timeout t]
import sys

from SocketTCP import SocketTCP

address = (sys.argv[1], int(sys.argv[2]))
SocketTCP.debug = "--debug" in sys.argv
if "--perdida" in sys.argv:
    SocketTCP.perdida = float(sys.argv[sys.argv.index("--perdida") + 1])
if "--timeout" in sys.argv:
    SocketTCP.timeout = float(sys.argv[sys.argv.index("--timeout") + 1])
mode = "go_back_n" if "--gbn" in sys.argv else "stop_and_wait"

client_socketTCP = SocketTCP()
client_socketTCP.connect(address)
client_socketTCP.set_congestion_control("--cc" in sys.argv)
# test 1
message = "Mensje de len=16".encode()
client_socketTCP.send(message, mode=mode)
# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode=mode)
# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode=mode)
# test 4
message = ("a" * 21 + "b" * 21).encode()
client_socketTCP.send(message, mode=mode)
# cierre de la conexion
client_socketTCP.close()
