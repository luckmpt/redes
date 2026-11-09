import socket
import util

socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    IP_router_final, puerto_router_final, mensaje = input("IP_router_final;puerto_router_final;mensaje : ").split(";")
    IP_envio, puerto_envio = input("IP_envio;puerto_envio : ").split(";")
    packete = util.create_packet((IP_router_final, int(puerto_router_final), mensaje.encode('utf-8')))
    socket.sendto(packete, (IP_envio, int(puerto_envio)))