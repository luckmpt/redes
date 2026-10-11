# Uso: python3 servidor.py <ip> <puerto> [--debug] [--perdida p]
import sys

from SocketTCP import SocketTCP

ip = sys.argv[1] if len(sys.argv) > 1 else "localhost"
puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
SocketTCP.debug = "--debug" in sys.argv
if "--perdida" in sys.argv:
    SocketTCP.perdida = float(sys.argv[sys.argv.index("--perdida") + 1])

servidor = SocketTCP()
servidor.bind((ip, puerto))
conexion, direccion = servidor.accept()

# recv corta en min(largo, buff_size), con un buff grande llega el archivo completo
datos = conexion.recv(10 ** 9)
sys.stdout.buffer.write(datos)
sys.stdout.flush()
conexion.recv_close()
