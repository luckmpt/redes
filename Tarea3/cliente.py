# Uso: python3 cliente.py <ip> <puerto> [--debug] [--perdida p] < archivo.txt
import sys

from SocketTCP import SocketTCP

ip = sys.argv[1]
puerto = int(sys.argv[2])
SocketTCP.debug = "--debug" in sys.argv
if "--perdida" in sys.argv:
    SocketTCP.perdida = float(sys.argv[sys.argv.index("--perdida") + 1])

# el archivo llega por stdin, se lee entero como bytes
datos = sys.stdin.buffer.read()

cliente = SocketTCP()
cliente.connect((ip, puerto))
cliente.send(datos)
cliente.close()
