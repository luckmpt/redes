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

rr = []
# paso 6: fragmentos que llegan a este router, agrupados por ID
fragmentos = {}

while True:
    packet, paquete_address = socket.recvfrom(1024)
    ip, port, TTL, ID, offset, tamano, FLAG, msj = util.parse_packet(packet)
    if ip == router_ip and port == router_port:
        fragmentos.setdefault(ID, []).append(packet)
        # paso 7: se intenta rearmar cada vez que llega algo; None = faltan fragmentos
        completo = util.reassemble_IP_packet(fragmentos[ID])
        if completo is not None:
            print(util.parse_packet(completo)[7].decode())
            del fragmentos[ID]
    elif TTL <= 0:
        print(f"Se recibió paquete {(ip, port)} con TTL 0")
    else:
        next_hop = util.check_routes(router_rutas, (ip, port), rr)
        if next_hop is not None:
            next_ip, next_port, MTU, rr = next_hop
            print(f"redirigiendo paquete {paquete_address} con destino final {(ip, port)} desde {(router_ip,router_port)} hacia {(next_ip, next_port)}")
            newPacket = util.create_packet((ip, port, TTL - 1, ID, offset, tamano, FLAG, msj))
            # se fragmenta segun el MTU del enlace por donde sale
            frags = util.fragment_IP_packet(newPacket, MTU)
            print(f"  {len(frags)} fragmento(s) por enlace con MTU {MTU}")
            for fragmento in frags:
                socket.sendto(fragmento, (next_ip, next_port))
        else:
            print(f"No hay rutas hacia {(ip, port)} para paquete {paquete_address}")
