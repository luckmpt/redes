# Uso: python3 cliente.py <ip> <puerto> [--gbn] [--cc] [--debug] [--perdida p] [--timeout t] < archivo
import sys
import time

from SocketTCP import SocketTCP

address = (sys.argv[1], int(sys.argv[2]))
SocketTCP.debug = "--debug" in sys.argv
if "--perdida" in sys.argv:
    SocketTCP.perdida = float(sys.argv[sys.argv.index("--perdida") + 1])
if "--timeout" in sys.argv:
    SocketTCP.timeout = float(sys.argv[sys.argv.index("--timeout") + 1])
mode = "go_back_n" if "--gbn" in sys.argv else "stop_and_wait"

# el archivo llega por stdin
message = sys.stdin.buffer.read()

client_socketTCP = SocketTCP()
client_socketTCP.connect(address)
client_socketTCP.set_congestion_control("--cc" in sys.argv)
inicio = time.time()
client_socketTCP.send(message, mode=mode)
print(f"segmentos enviados: {client_socketTCP.number_of_sent_segments}, tiempo: {time.time() - inicio:.2f}s")
client_socketTCP.close()
