import socket

if __name__ == "__main__":
    msj = input("Ingrese un mensaje: ")

    socket_address = ('localhost', 5000)

    tamano_buffer = len(msj)

    mensaje_completo = ''

    while len(mensaje_completo) < tamano_buffer:

        print('Creando socket - Cliente')
        # armamos el socket
        socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        socket_cliente.sendto(msj.encode(), socket_address)

        mensaje, address = socket_cliente.recvfrom(tamano_buffer)

        mensaje_completo += mensaje.decode()
        msj = msj[len(mensaje.decode()):]

    print(f' -> Se ha recibido el siguiente mensaje: {mensaje_completo}')

    socket_cliente.close()
