import socket
import util

socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    IP_router_final, puerto_router_final, TTL, ID, mensaje = input("IP_router_final;puerto_router_final;TTL;ID;mensaje : ").split(";", 4)
    IP_envio, puerto_envio = input("IP_envio;puerto_envio : ").split(";")
    datos = mensaje.encode('utf-8')
    # paquete sin fragmentar: offset 0 y FLAG 0
    packete = util.create_packet((IP_router_final, int(puerto_router_final), int(TTL), int(ID), 0, len(datos), 0, datos))
    socket.sendto(packete, (IP_envio, int(puerto_envio)))
