

# fin de linea en HTTP
CRLF = b"\r\n"
# fin de la seccion de headers
HEADERS_END = b"\r\n\r\n"

"""Convierte un mensaje HTTP en bytes a un diccionario."""
def parse_HTTP_message(http_message: bytes) -> dict:
    
    # separamos headers y body en el primer \r\n\r\n
    head, separator, body = http_message.partition(HEADERS_END)
    # si no aparecio el marcador, el mensaje no trae body
    if not separator:
        head, body = http_message.rstrip(CRLF), b""
    # cada linea de la seccion de headers va separada por \r\n
    lines = head.split(CRLF)
    # la primera linea es la start line
    start_line = lines[0].decode("latin-1")
    # guardamos los headers como pares (nombre, valor)
    headers = {}
    # las lineas restantes son un header cada una
    for line in lines[1:]:
        # saltamos lineas vacias
        if not line:
            continue
        # partition y no split: el valor puede contener ":"
        name, sep, value = line.decode("latin-1").partition(":")
        # sin ":" no es un header valido
        if not sep:
            continue
        # guardamos sin espacios sobrantes
        headers[name.strip()] = value.strip()
    # estructura de datos que devolvemos
    parsed = {"start_line": start_line, "headers": headers, "body": body}
    # la start line tiene tres campos separados por espacio
    parts = start_line.split(" ", 2)
    # si empieza con HTTP/ es una respuesta
    if start_line.startswith("HTTP/"):
        parsed["type"] = "response"
        parsed["version"] = parts[0]
        parsed["status_code"] = parts[1] if len(parts) > 1 else ""
        parsed["reason"] = parts[2] if len(parts) > 2 else ""
    # si no, es una peticion
    else:
        parsed["type"] = "request"
        parsed["method"] = parts[0]
        parsed["target"] = parts[1] if len(parts) > 1 else "/"
        parsed["version"] = parts[2] if len(parts) > 2 else "HTTP/1.1"
    return parsed

"""Convierte el diccionario de parse_HTTP_message de vuelta a bytes."""

def create_HTTP_message(parsed: dict) -> bytes:
        
    # la start line se arma distinto segun el tipo de mensaje
    if parsed.get("type") == "response":
        start_line = "{} {} {}".format(parsed["version"], parsed["status_code"], parsed["reason"])
    else:
        start_line = "{} {} {}".format(parsed["method"], parsed["target"], parsed["version"])
    # la start line termina en \r\n
    message = start_line.rstrip().encode("latin-1") + CRLF
    # cada header ocupa una linea
    for name in parsed["headers"]:
        message += "{}: {}".format(name, parsed["headers"][name]).encode("latin-1") + CRLF
    # linea vacia: marca el fin de los headers
    message += CRLF
    # el body se concatena tal cual, en bytes
    return message + parsed.get("body", b"")

def get_header(parsed, name):
    """Busca un header sin distinguir mayusculas. Devuelve None si no esta."""
    for key in parsed["headers"]:
        if key.lower() == name.lower():
            return parsed["headers"][key]
    return None


def del_header(parsed, name):
    """Elimina un header sin distinguir mayusculas."""
    for key in list(parsed["headers"]):
        if key.lower() == name.lower():
            del parsed["headers"][key]


def recv_n(sock, buff_size, buffer, n):
    """Sigue recibiendo hasta juntar n bytes (o hasta que cierren)."""
    while len(buffer) < n:
        chunk = sock.recv(buff_size)
        if not chunk:
            break
        buffer += chunk
    return buffer


def recv_chunked(sock, buff_size, buffer):
    """Lee un body con Transfer-Encoding: chunked y lo devuelve armado."""
    body = b""
    while True:
        # cada chunk empieza con su largo en hexadecimal y un \r\n
        while CRLF not in buffer:
            chunk = sock.recv(buff_size)
            if not chunk:
                return body
            buffer += chunk
        linea, _, buffer = buffer.partition(CRLF)
        largo = int(linea.split(b";")[0].strip(), 16)
        # el chunk de largo 0 marca el final
        if largo == 0:
            return body
        buffer = recv_n(sock, buff_size, buffer, largo + 2)
        body += buffer[:largo]
        # +2 para saltarse el \r\n que cierra el chunk
        buffer = buffer[largo + 2:]


def recv_HTTP_message(sock, buff_size, con_body=True):
    """Recibe un mensaje HTTP completo, con un buffer de cualquier tamano."""
    data = b""
    # los headers estan completos recien cuando aparece \r\n\r\n
    while HEADERS_END not in data:
        chunk = sock.recv(buff_size)
        if not chunk:
            break
        data += chunk
    if not data:
        return None
    head, _, body = data.partition(HEADERS_END)
    parsed = parse_HTTP_message(head + HEADERS_END)

    largo = get_header(parsed, "Content-Length")
    chunked = get_header(parsed, "Transfer-Encoding")
    if not con_body:
        body = b""
    elif chunked and "chunked" in chunked.lower():
        body = recv_chunked(sock, buff_size, body)
        del_header(parsed, "Transfer-Encoding")
        parsed["headers"]["Content-Length"] = str(len(body))
    elif largo is not None:
        body = recv_n(sock, buff_size, body, int(largo))[:int(largo)]
    elif parsed["type"] == "response":
        # sin Content-Length ni chunked, el mensaje termina cuando cierran
        while True:
            chunk = sock.recv(buff_size)
            if not chunk:
                break
            body += chunk
        parsed["headers"]["Content-Length"] = str(len(body))
    else:
        body = b""
    parsed["body"] = body
    return parsed
