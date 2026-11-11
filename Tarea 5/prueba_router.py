import socket
import util
import sys

if len(sys.argv) >= 4:
    headers = sys.argv[1]
    IP_inicial = sys.argv[2]
    puerto_inicial = int(sys.argv[3])
else:
    print("Usar: python3 prueba_router.py headers IP_router_inicial puerto_router_inicial")
    sys.exit(1)

ip_final, puerto_final, TTL = headers.split(";")

socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

with open("archivo.txt", "r") as archivo:
    for linea in archivo:
        paquete = util.create_packet((ip_final, int(puerto_final), int(TTL), linea.encode('utf-8')))
        socket.sendto(paquete, (IP_inicial, puerto_inicial))
