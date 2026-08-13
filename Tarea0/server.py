import socket

if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 4
    new_socket_address = ('localhost', 5000)

    print('Creando socket - Servidor')
    # armamos el socket
    # los parámetros que recibe el socket indican el tipo de conexión
    # socket.SOCK_DGRAM = socket no orientado a conexión
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(new_socket_address)

    # nos quedamos esperando a que llegue una petición de conexión
    print('... Esperando clientes')
    while True:
        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
        message, address = server_socket.recvfrom(buff_size)

        print(f' -> Se ha recibido el siguiente mensaje: {message.decode()}')

        # el mensaje debe pasarse a bytes antes de ser enviado, para ello usamos encode
        server_socket.sendto(message, address)

        # seguimos esperando por si llegan otras conexiones