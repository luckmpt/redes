import socket
from dnslib import DNSRecord
from dnslib.dns import CLASS, QTYPE
import dnslib

root_ip = "198.41.0.4"

def parsearDNS(data):
    d = DNSRecord.parse(data)
    qname = d.get_q().get_qname().label

    header = d.header
    ancount = header.a
    nscount = header.auth
    arcount = header.ar

    Answer = {}
    if ancount > 0:
        Answer["all_RR"] = d.rr  # lista de objetos tipo dnslib.dns.RR
        first_answer = d.get_a()
        Answer["first"] = first_answer  # primer objeto en la lista all_resource_records
        Answer["domain_name"] = first_answer.get_rname()  # nombre de dominio por el cual se está respondiendo
        Answer["class"] = CLASS.get(first_answer.rclass)
        Answer["type"] = QTYPE.get(first_answer.rtype)
        Answer["data"] = first_answer.rdata  # rdata asociada a la respuesta

    Authority = []
    if nscount > 0:
        authority_section_list = d.auth  # contiene un total de number_of_authority_elements
        if len(authority_section_list) > 0:
            for auth in authority_section_list:
                authority = {}
                authority["first"] = auth
                authority["type"] = QTYPE.get(auth.rtype)
                authority["class"] = CLASS.get(auth.rclass)
                authority["time_to_live"] = auth.ttl
                auth_data = auth.rdata
                authority["rdata"] = auth_data
                # si recibimos auth_type = 'SOA' este es un objeto tipo dnslib.dns.SOA
                if isinstance(auth_data, dnslib.dns.SOA):
                    authority["primary_name_server"] = auth_data.get_mname()  # servidor de nombre primario
                elif isinstance(auth_data, dnslib.dns.NS): # si en vez de SOA recibimos un registro tipo NS
                    authority["name_server_domain"] = auth_data  # entonces authority_section_0_rdata contiene el nombre de dominio del primer servidor de nombre de la lista
                Authority.append(authority)

    Additionals = []
    if arcount > 0:
        additional_records = d.ar  # lista que contiene un total de number_of_additional_elements DNS records
        for add in additional_records:
            additional = {}
            # En caso de tener additional records, estos pueden contener la IP asociada a elementos del authority section
            additional["class"] = CLASS.get(add.rclass)
            additional_type = QTYPE.get(add.rclass)  # para saber si esto es asi debemos revisar el tipo de record
            additional["type"] = additional_type
            if additional_type == 'A': # si el tipo es 'A' (Address)
                additional["rname"] = add.rname  # nombre de dominio
                additional["rdata"] = add.rdata  # IP asociada
            Additionals.append(additional)

    parse = {
          "QName": qname,
          "ANCOUNT": ancount,
          "NSCOUNT": nscount,
          "ARCOUNT": arcount,
          "Answer": Answer,
          "Authority": Authority,
          "Additional": Additionals
    }
    return parse

def resolver(mensaje_consulta: bytes, ip_addr=root_ip) -> bytes:
    resolver_address = (ip_addr, 53)
    sock_resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"Enviando mensaje a {ip_addr}:53")
    try:
        # lo enviamos, hacemos cast a bytes de lo que resulte de la función pack() sobre el mensaje
        sock_resolver.sendto(mensaje_consulta, resolver_address)
        # En data quedará la respuesta a nuestra consulta
        data, _ = sock_resolver.recvfrom(4096)
        d = parsearDNS(data)
        if d["ANCOUNT"] > 0:
            if d["Answer"]["type"] == "A":
                print(f"Respuesta encontrada")
                return data
        if d["NSCOUNT"] > 0 and d["ARCOUNT"] > 0:
            for add in d["Additional"]:
                if add["type"] == "A":
                    print(f"Resolviendo {add['rname']}")
                    return resolver(mensaje_consulta, add["rdata"])
        if d["NSCOUNT"] > 0:
            for auth in d["Authority"]:
                if auth["type"] == "SOA":
                    name_server = auth["primary_name_server"]
                    print(f"Resolviendo {name_server}")
                    ip_name_server = resolver(bytes(DNSRecord.question(name_server).pack()))
                    return resolver(mensaje_consulta, ip_name_server)
        # ignorar otro tipo de respuesta, RESPONDER EN INFORME ¿Qué limitaciones puede presentar esto?.

    finally:
        print(f"Cerrando socket con {ip_addr}:53")
        sock_resolver.close()
    # Ojo que los datos de la respuesta van en en una estructura de datos
    return d

ip_addres = "10.172.47.71"
server_address = (ip_addres, 8000)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # RESPONDER EN INFORME porque socket no orientado a conexion.
sock.bind(server_address)
print(f"Servidor DNS escuchando en {ip_addres}:8000")
while True:
        data, address = sock.recvfrom(4096)
        print(f"Recibido mensaje de {address}")
        respuesta = resolver(data)
        if respuesta:
            sock.sendto(respuesta, address)
