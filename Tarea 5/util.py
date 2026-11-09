################ Item 4 #########################

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

# Test
IP_packet_v1 = b'\x7f\x00\x00\x01\x22\xb1ojala que pase'
parsed_IP_packet = parse_packet(IP_packet_v1)
IP_packet_v2 = create_packet(parsed_IP_packet)
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))

################# Item 6 #########################

def check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str, int] | None:
    with open(routes_file_name, 'r') as routes_file:
        for line in routes_file:
            ip_destino, primer_puertp, ultimo_puerto, ip_siguiente, puerto_siguiente = line.strip().split(" ")
            ip_destino, _ = ip_destino.split("/")
            if ip_destino == destination_address[0] and int(primer_puertp) <= destination_address[1] <= int(ultimo_puerto):
                return (ip_siguiente, int(puerto_siguiente))
    return None

# test
assert check_routes("rutas_R1_v2.txt", ("127.0.0.1", 8882)) == ("127.0.0.1", 8882)
assert check_routes("rutas_R1_v2.txt", ("127.0.0.1", 8883)) == ("127.0.0.1", 8882)
assert check_routes("rutas_R1_v2.txt", ("127.0.0.1", 8884)) == None
assert check_routes("rutas_R2_v2.txt", ("127.0.0.1", 8881)) == ("127.0.0.1", 8881)
assert check_routes("rutas_R2_v2.txt", ("127.0.0.1", 8883)) == ("127.0.0.1", 8883)
assert check_routes("rutas_R2_v2.txt", ("127.0.0.1", 8884)) == None
assert check_routes("rutas_R3_v2.txt", ("127.0.0.1", 8881)) == ("127.0.0.1", 8882)
assert check_routes("rutas_R3_v2.txt", ("127.0.0.1", 8882)) == ("127.0.0.1", 8882)
assert check_routes("rutas_R3_v2.txt", ("127.0.0.1", 8884)) == None