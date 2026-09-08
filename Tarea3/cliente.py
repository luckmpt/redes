import socket

nombre_archivo = input("Ingrese el nombre del archivo: ")

archivo = open(nombre_archivo, "rb")
contenido = archivo.read()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
i = 0
while i < len(contenido):
    print(f"Enviando: {contenido[i:i+16]}")
    sock.sendto(contenido[i:i+16], ("localhost", 8000))
    i += 16

print("Enviando fin de archivo")
sock.sendto(b'FIN DEL ARCHIVO', ("localhost", 8000))
sock.close()
