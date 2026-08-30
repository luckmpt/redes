# Tarea 2: resolver DNS
# Uso: python3 resolver.py [ip] [puerto] [--debug]

import socket
import sys

import dnslib
from dnslib import DNSRecord
from dnslib.dns import CLASS, QTYPE

root_ip = "198.41.0.4"
timeout = 5
max_profundidad = 20

ip_addres = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
DEBUG = "--debug" in sys.argv

# ultimas 20 consultas recibidas y cache de los 3 dominios mas repetidos
historial = []
cache = {}


def debug(mensaje):
    if DEBUG:
        print(f"(debug) {mensaje}")


# pasa un mensaje DNS en bytes a un diccionario
def parsearDNS(data):
    d = DNSRecord.parse(data)
    qname = d.get_q().get_qname().label

    header = d.header
    ancount = header.a
    nscount = header.auth
    arcount = header.ar

    Answer = {}
    if ancount > 0:
        Answer["all_RR"] = d.rr
        first_answer = d.get_a()
        Answer["first"] = first_answer
        Answer["domain_name"] = first_answer.get_rname()
        Answer["class"] = CLASS.get(first_answer.rclass)
        Answer["type"] = QTYPE.get(first_answer.rtype)
        Answer["data"] = first_answer.rdata

    Authority = []
    if nscount > 0:
        for auth in d.auth:
            authority = {}
            authority["first"] = auth
            authority["type"] = QTYPE.get(auth.rtype)
            authority["class"] = CLASS.get(auth.rclass)
            authority["time_to_live"] = auth.ttl
            auth_data = auth.rdata
            authority["rdata"] = auth_data
            if isinstance(auth_data, dnslib.dns.SOA):
                authority["primary_name_server"] = auth_data.get_mname()
            elif isinstance(auth_data, dnslib.dns.NS):
                authority["name_server_domain"] = auth_data
            Authority.append(authority)

    Additionals = []
    if arcount > 0:
        for add in d.ar:
            additional = {}
            additional["class"] = CLASS.get(add.rclass)
            # rtype y no rclass: con rclass todo record IN parece tipo A
            additional_type = QTYPE.get(add.rtype)
            additional["type"] = additional_type
            if additional_type == "A":
                additional["rname"] = add.rname
                additional["rdata"] = add.rdata
            Additionals.append(additional)

    return {
        "QName": qname,
        "ANCOUNT": ancount,
        "NSCOUNT": nscount,
        "ARCOUNT": arcount,
        "Answer": Answer,
        "Authority": Authority,
        "Additional": Additionals,
    }


# manda la consulta por UDP, devuelve None si el servidor no contesta
def enviar_query(mensaje_consulta, ip_addr):
    sock_resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_resolver.settimeout(timeout)
    try:
        sock_resolver.sendto(mensaje_consulta, (ip_addr, 53))
        data, _ = sock_resolver.recvfrom(4096)
        return data
    except (socket.timeout, OSError) as error:
        debug(f"sin respuesta de {ip_addr}: {error}")
        return None
    finally:
        sock_resolver.close()


# saca la primera IP de tipo A de la seccion Answer
def primera_ip(respuesta):
    d = DNSRecord.parse(respuesta)
    for rr in d.rr:
        if QTYPE.get(rr.rtype) == "A":
            return str(rr.rdata)
    return None


# resuelve la consulta preguntando desde la raiz hacia abajo
def resolver(mensaje_consulta: bytes, ip_addr=root_ip, ns_name=".", profundidad=0) -> bytes:
    if profundidad > max_profundidad:
        return None

    qname = str(DNSRecord.parse(mensaje_consulta).get_q().get_qname())
    debug(f"Consultando '{qname}' a '{ns_name}' con direccion IP '{ip_addr}'")

    respuesta = enviar_query(mensaje_consulta, ip_addr)
    if respuesta is None:
        return None

    d = parsearDNS(respuesta)

    # b) la respuesta trae un registro A, ya terminamos
    if d["ANCOUNT"] > 0:
        for rr in d["Answer"]["all_RR"]:
            if QTYPE.get(rr.rtype) == "A":
                return respuesta
        # hay Answer pero sin ningun A (por ejemplo un CNAME solo): se ignora
        debug(f"respuesta sin registros A para '{qname}', se ignora")
        return None

    # c) delegacion a otro name server
    if d["NSCOUNT"] > 0:
        # c.i) la IP del name server viene en Additional
        for add in d["Additional"]:
            if add["type"] == "A":
                return resolver(mensaje_consulta, str(add["rdata"]), str(add["rname"]), profundidad + 1)

        # c.ii) no viene la IP, hay que resolver el nombre del name server
        for auth in d["Authority"]:
            if auth["type"] == "NS":
                ns = str(auth["rdata"])
                debug(f"sin IP en Additional, resolviendo el name server '{ns}'")
                respuesta_ns = resolver(bytes(DNSRecord.question(ns).pack()), root_ip, ".", profundidad + 1)
                if respuesta_ns:
                    ip_ns = primera_ip(respuesta_ns)
                    if ip_ns:
                        return resolver(mensaje_consulta, ip_ns, ns, profundidad + 1)

    # d) cualquier otro tipo de respuesta se ignora
    return None


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # DNS usa UDP
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((ip_addres, puerto))
print(f"Resolver escuchando en {ip_addres}:{puerto}" + (" (modo debug)" if DEBUG else ""))

while True:
    data, address = sock.recvfrom(4096)
    consulta = DNSRecord.parse(data)
    qname = str(consulta.get_q().get_qname())

    # el cache guarda solo los 3 dominios mas repetidos de las ultimas 20 consultas
    historial.append(qname)
    if len(historial) > 20:
        historial.pop(0)

    # contamos cuantas veces aparece cada dominio en las ultimas 20 consultas
    conteo = {}
    for dominio in historial:
        conteo[dominio] = conteo.get(dominio, 0) + 1
    mas_repetidos = sorted(conteo, key=lambda d: conteo[d], reverse=True)[:3]
    for dominio in list(cache):
        if dominio not in mas_repetidos:
            del cache[dominio]

    if qname in cache:
        debug(f"'{qname}' respondido desde el cache")
        guardada = DNSRecord.parse(cache[qname])
        # el ID debe ser el de la consulta nueva, si no dig descarta la respuesta
        guardada.header.id = consulta.header.id
        sock.sendto(guardada.pack(), address)
        continue

    respuesta = resolver(data)
    if respuesta:
        if qname in mas_repetidos:
            cache[qname] = respuesta
        sock.sendto(respuesta, address)
    else:
        debug(f"no se pudo resolver '{qname}'")
