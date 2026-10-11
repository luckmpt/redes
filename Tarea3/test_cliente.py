# Uso: python3 test_cliente.py <ip> <puerto> [--debug] [--perdida p]
import sys

from SocketTCP import SocketTCP

address = (sys.argv[1], int(sys.argv[2]))
SocketTCP.debug = "--debug" in sys.argv
if "--perdida" in sys.argv:
    SocketTCP.perdida = float(sys.argv[sys.argv.index("--perdida") + 1])

client_socketTCP = SocketTCP()
client_socketTCP.connect(address)
# test 1
message = "Mensje de len=16".encode()
client_socketTCP.send(message)
# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)
# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)
# test 4: 2n bytes con n=21, que no es multiplo de 16
message = ("a" * 21 + "b" * 21).encode()
client_socketTCP.send(message)
# test 5: buff_size mucho menor que un segmento, sobra mas de un buff
message = "0123456789abcdefghijklmnopqrstuvwxyzABCD".encode()
client_socketTCP.send(message)
# cierre de la conexion
client_socketTCP.close()
