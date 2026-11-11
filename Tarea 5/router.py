import sys
import socket
import util

if len(sys.argv) >= 4:
    router_ip = sys.argv[1]
    router_port = int(sys.argv[2])
    router_rutas = sys.argv[3]

else:
    print("Usage: python3 router.py router_IP router_puerto router_rutas.txt")
    sys.exit(1)

socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind((router_ip, router_port))

while True:
    packet, paquete_address = socket.recvfrom(1024)
    ip, port, msj = util.parse_packet(packet)
    if ip == router_ip and port == router_port:
        print(msj.decode())
    else:
        next_hop = util.check_routes(router_rutas, (ip, port))
        if next_hop is not None:
            next_ip, next_port = next_hop
            print(f"redirigiendo paquete {packet} con destino final {(ip, port)} desde {(router_ip,router_port)} hacia {next_hop}")
            socket.sendto(packet, (next_ip, next_port))
        else:
            print(f"No hay rutas hacia {(ip, port)} para paquete {packet}")
