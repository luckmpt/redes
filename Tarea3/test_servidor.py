# Uso: python3 test_servidor.py <ip> <puerto> [--debug] [--perdida p]
import sys

from SocketTCP import SocketTCP

address = (sys.argv[1], int(sys.argv[2]))
SocketTCP.debug = "--debug" in sys.argv
if "--perdida" in sys.argv:
    SocketTCP.perdida = float(sys.argv[sys.argv.index("--perdida") + 1])

server_socketTCP = SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()

# test 1
buff_size = 16
full_message = connection_socketTCP.recv(buff_size)
print("Test 1 received:", full_message)
if full_message == "Mensje de len=16".encode(): print("Test 1: Passed")
else: print("Test 1: Failed")

# test 2
buff_size = 19
full_message = connection_socketTCP.recv(buff_size)
print("Test 2 received:", full_message)
if full_message == "Mensaje de largo 19".encode(): print("Test 2: Passed")
else: print("Test 2: Failed")

# test 3
buff_size = 14
message_part_1 = connection_socketTCP.recv(buff_size)
message_part_2 = connection_socketTCP.recv(buff_size)
print("Test 3 received:", message_part_1 + message_part_2)
if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode(): print("Test 3: Passed")
else: print("Test 3: Failed")

# test 4: dos recv de n=21 para un mensaje de 2n
part_1 = connection_socketTCP.recv(21)
part_2 = connection_socketTCP.recv(21)
print("Test 4 received:", part_1, part_2)
if part_1 == ("a" * 21).encode() and part_2 == ("b" * 21).encode(): print("Test 4: Passed")
else: print("Test 4: Failed")

# test 5: ocho recv de 5 bytes, ninguno puede pasarse de buff_size
parts = [connection_socketTCP.recv(5) for i in range(8)]
print("Test 5 received:", parts)
if b"".join(parts) == "0123456789abcdefghijklmnopqrstuvwxyzABCD".encode() and all(len(x) == 5 for x in parts): print("Test 5: Passed")
else: print("Test 5: Failed")

# cierre de la conexion
connection_socketTCP.recv_close()
