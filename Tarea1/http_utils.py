

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
    headers = []
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
        headers.append((name.strip(), value.strip()))
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
    for name, value in parsed.get("headers", []):
        message += "{}: {}".format(name, value).encode("latin-1") + CRLF
    # linea vacia: marca el fin de los headers
    message += CRLF
    # el body se concatena tal cual, en bytes
    return message + parsed.get("body", b"")