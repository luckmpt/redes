import socket
import sys
import util

# test paso 7: 2 paquetes con distinto ID fragmentados a mano y enviados directo a R5
if len(sys.argv) < 2:
    print("Usar: python3 prueba_fragmentos.py orden|desorden|intercalado")
    sys.exit(1)
modo = sys.argv[1]
destino = ("127.0.0.1", 8885)

m1 = b"paquete 1: este mensaje es largo para que se fragmente en varios trozos"
m2 = b"paquete 2: otro mensaje distinto, con otro ID, tambien fragmentado"
p1 = util.create_packet(("127.0.0.1", 8885, 10, 1, 0, len(m1), 0, m1))
p2 = util.create_packet(("127.0.0.1", 8885, 10, 2, 0, len(m2), 0, m2))
f1 = util.fragment_IP_packet(p1, 50)
f2 = util.fragment_IP_packet(p2, 50)

if modo == "orden":
    envio = f1 + f2
elif modo == "desorden":
    # orden fijo distinto al original para que siempre llegue desordenado
    envio = [f1[2], f1[0], f2[1], f1[1], f2[2], f2[0]]
else:
    # se alternan fragmentos de ID 1 e ID 2
    envio = []
    for i in range(max(len(f1), len(f2))):
        envio += f1[i:i+1] + f2[i:i+1]

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for f in envio:
    _, _, _, ID, offset, tamano, FLAG, _ = util.parse_packet(f)
    print(f"enviando ID={ID} offset={offset} tamaño={tamano} FLAG={FLAG}")
    s.sendto(f, destino)
