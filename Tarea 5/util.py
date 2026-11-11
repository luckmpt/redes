################ Item 4 #########################
# header: 4 bytes de IP y 2 de puerto, despues el mensaje

def parse_packet(IP_packet: bytes):
    a = IP_packet[0]
    b = IP_packet[1]
    c = IP_packet[2]
    d = IP_packet[3]
    ipv4 = f"{a}.{b}.{c}.{d}"
    port = int.from_bytes(IP_packet[4:6], byteorder="big")
    mensaje = IP_packet[6:]
    return (ipv4, port, mensaje)

def create_packet(parsed_IP_packet):
    ipv4 = parsed_IP_packet[0]
    port = parsed_IP_packet[1]
    mensaje = parsed_IP_packet[2]
    a, b, c, d = map(int, ipv4.split('.'))
    packet = bytes([a, b, c, d]) + port.to_bytes(2, byteorder="big") + mensaje
    return packet

################# Item 6 y 8 #########################
import ipaddress

# round-robin: por cada area de la red (red + rango de puertos) se guarda la ultima ruta usada
ultima_ruta = {}

def check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str, int] | None:
    area = None
    rutas = []
    with open(routes_file_name, 'r') as routes_file:
        for line in routes_file:
            if not line.strip():
                continue
            red, primer_puerto, ultimo_puerto, ip_siguiente, puerto_siguiente = line.strip().split(" ")
            en_red = ipaddress.ip_address(destination_address[0]) in ipaddress.ip_network(red, strict=False)
            if en_red and int(primer_puerto) <= destination_address[1] <= int(ultimo_puerto):
                # la primera linea que calza define el area, y se juntan todas las rutas de esa area
                if area is None:
                    area = (red, primer_puerto, ultimo_puerto)
                if (red, primer_puerto, ultimo_puerto) == area:
                    rutas.append((ip_siguiente, int(puerto_siguiente)))
    if area is None:
        return None
    i = (ultima_ruta.get(area, -1) + 1) % len(rutas)
    ultima_ruta[area] = i
    return rutas[i]

# los tests corren solo si se ejecuta util.py directo, no al importarlo desde router.py
if __name__ == "__main__":
    IP_packet_v1 = b'\x7f\x00\x00\x01\x22\xb1ojala que pase'
    parsed_IP_packet = parse_packet(IP_packet_v1)
    IP_packet_v2 = create_packet(parsed_IP_packet)
    print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))

    assert check_routes("rutas_R1_v2.txt", ("127.0.0.1", 8882)) == ("127.0.0.1", 8882)
    assert check_routes("rutas_R1_v2.txt", ("127.0.0.1", 8883)) == ("127.0.0.1", 8882)
    assert check_routes("rutas_R1_v2.txt", ("127.0.0.1", 8884)) == None
    assert check_routes("rutas_R2_v2.txt", ("127.0.0.1", 8881)) == ("127.0.0.1", 8881)
    assert check_routes("rutas_R2_v2.txt", ("127.0.0.1", 8883)) == ("127.0.0.1", 8883)
    assert check_routes("rutas_R2_v2.txt", ("127.0.0.1", 8884)) == None
    assert check_routes("rutas_R3_v2.txt", ("127.0.0.1", 8881)) == ("127.0.0.1", 8882)
    assert check_routes("rutas_R3_v2.txt", ("127.0.0.1", 8882)) == ("127.0.0.1", 8882)
    assert check_routes("rutas_R3_v2.txt", ("127.0.0.1", 8884)) == None
    # round-robin: R2 alterna entre R3 y R4 para llegar a R5
    assert check_routes("rutas_R2_v3.txt", ("127.0.0.1", 8885)) == ("127.0.0.1", 8883)
    assert check_routes("rutas_R2_v3.txt", ("127.0.0.1", 8885)) == ("127.0.0.1", 8884)
    assert check_routes("rutas_R2_v3.txt", ("127.0.0.1", 8885)) == ("127.0.0.1", 8883)
    print("check_routes OK")
