################ Item 1 #########################
# header de 20 bytes: IP (4), puerto (2), TTL (1), ID (4), offset (4), tamaño (4), FLAG (1)
HEADER = 20

def parse_packet(IP_packet: bytes):
    a = IP_packet[0]
    b = IP_packet[1]
    c = IP_packet[2]
    d = IP_packet[3]
    ipv4 = f"{a}.{b}.{c}.{d}"
    port = int.from_bytes(IP_packet[4:6], byteorder="big")
    TTL = IP_packet[6]
    ID = int.from_bytes(IP_packet[7:11], byteorder="big")
    offset = int.from_bytes(IP_packet[11:15], byteorder="big")
    tamano = int.from_bytes(IP_packet[15:19], byteorder="big")
    FLAG = IP_packet[19]
    mensaje = IP_packet[20:]
    return (ipv4, port, TTL, ID, offset, tamano, FLAG, mensaje)

def create_packet(parsed_IP_packet):
    ipv4, port, TTL, ID, offset, tamano, FLAG, mensaje = parsed_IP_packet
    a, b, c, d = map(int, ipv4.split('.'))
    packet = bytes([a, b, c, d]) + port.to_bytes(2, byteorder="big") + TTL.to_bytes(1, byteorder="big")
    packet += ID.to_bytes(4, byteorder="big") + offset.to_bytes(4, byteorder="big")
    packet += tamano.to_bytes(4, byteorder="big") + FLAG.to_bytes(1, byteorder="big") + mensaje
    return packet

################# Item 2 #########################

def check_routes(routes_file_name: str, destination_address: tuple[str, int], rr: list[str]):
    with open(routes_file_name, 'r') as routes_file:
        primero = None
        for line in routes_file:
            if line.strip() == "" or line.startswith("#"):
                continue
            ip_destino, primer_puertp, ultimo_puerto, ip_siguiente, puerto_siguiente, MTU = line.strip().split(" ")
            # la tabla de R5 del enunciado viene sin mascara
            ip_destino = ip_destino.split("/")[0]
            if ip_destino == destination_address[0] and int(primer_puertp) <= destination_address[1] <= int(ultimo_puerto):
                if puerto_siguiente in rr:
                    if primero is None:
                        primero = [ip_siguiente, puerto_siguiente, MTU]
                else:
                    rr.append(puerto_siguiente)
                    return (ip_siguiente, int(puerto_siguiente), int(MTU), rr)
        if primero is not None:
            rr = [primero[1]]
            return (primero[0], int(primero[1]), int(primero[2]), rr)
    return None

################# Item 3 #########################

def fragment_IP_packet(IP_packet: bytes, MTU: int) -> list[bytes]:
    if len(IP_packet) <= MTU:
        return [IP_packet]
    ip, port, TTL, ID, offset, tamano, FLAG, mensaje = parse_packet(IP_packet)
    trozo = MTU - HEADER
    fragmentos = []
    for i in range(0, len(mensaje), trozo):
        parte = mensaje[i:i + trozo]
        # el ultimo trozo hereda el FLAG original, asi un fragmento se puede volver a fragmentar
        ultimo = i + trozo >= len(mensaje)
        flag = FLAG if ultimo else 1
        fragmentos.append(create_packet((ip, port, TTL, ID, offset + i, len(parte), flag, parte)))
    return fragmentos

################# Item 5 #########################

def reassemble_IP_packet(fragment_list: list[bytes]) -> bytes | None:
    fragmentos = [parse_packet(f) for f in fragment_list]
    # se ordenan por offset porque pueden llegar en desorden
    fragmentos.sort(key=lambda f: f[4])
    mensaje = b""
    siguiente = 0
    for f in fragmentos:
        offset, tamano, msj = f[4], f[5], f[7]
        # si hay un hueco entre fragmentos todavia falta alguno
        if offset != siguiente:
            return None
        mensaje += msj
        siguiente = offset + tamano
    # el ultimo debe tener FLAG 0, si no faltan fragmentos al final
    if fragmentos[-1][6] != 0:
        return None
    ip, port, TTL, ID = fragmentos[0][:4]
    return create_packet((ip, port, TTL, ID, 0, len(mensaje), 0, mensaje))

if __name__ == "__main__":
    IP_packet_v1 = create_packet(("127.0.0.1", 8885, 10, 347, 0, 5, 0, b"hola!"))
    parsed_IP_packet = parse_packet(IP_packet_v1)
    assert parsed_IP_packet == ("127.0.0.1", 8885, 10, 347, 0, 5, 0, b"hola!")
    IP_packet_v2 = create_packet(parsed_IP_packet)
    print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))

    rr = []
    assert check_routes("rutas_R1_v3_mtu.txt", ("127.0.0.1", 8885), rr)[:3] == ("127.0.0.1", 8882, 100)
    assert check_routes("rutas_R5_v3_mtu.txt", ("127.0.0.1", 8881), [])[:3] == ("127.0.0.1", 8884, 140)
    print("check_routes con MTU OK")

    mensaje = bytes(range(130))
    grande = create_packet(("127.0.0.1", 8885, 10, 1, 0, len(mensaje), 0, mensaje))
    print("paquete de", len(grande), "bytes")
    assert fragment_IP_packet(grande, 200) == [grande]
    for MTU in (100, 80, 55, 50):
        frags = fragment_IP_packet(grande, MTU)
        datos = b"".join(parse_packet(f)[7] for f in frags)
        assert all(len(f) <= MTU for f in frags) and datos == mensaje
        print(f"MTU {MTU}: {len(frags)} fragmentos", [(parse_packet(f)[4], parse_packet(f)[5], parse_packet(f)[6]) for f in frags])
    # un fragmento se vuelve a fragmentar: (offset, tamaño, FLAG) siguen siendo consistentes
    refrag = [g for f in fragment_IP_packet(grande, 100) for g in fragment_IP_packet(f, 50)]
    print("re-fragmentado 100 -> 50:", [(parse_packet(f)[4], parse_packet(f)[5], parse_packet(f)[6]) for f in refrag])

    import random
    for MTU in (100, 80, 55, 50):
        fragment_list = fragment_IP_packet(grande, MTU)
        random.shuffle(fragment_list)
        IP_packet_v2 = reassemble_IP_packet(fragment_list)
        print(f"MTU {MTU} en desorden: IP_packet_v1 = IP_packet_v2 ? {grande == IP_packet_v2}")
    print("re-fragmentado:", reassemble_IP_packet(refrag) == grande)
    print("paquete sin fragmentar:", reassemble_IP_packet([IP_packet_v1]) == IP_packet_v1)
    print("falta un fragmento (devuelve None):", reassemble_IP_packet(refrag[:2] + refrag[3:]) is None)
    print("falta el ultimo (devuelve None):", reassemble_IP_packet(refrag[:-1]) is None)
