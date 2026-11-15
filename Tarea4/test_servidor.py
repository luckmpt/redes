# Uso: python3 test_servidor.py <ip> <puerto> [--gbn] [--debug] [--perdida p] [--timeout t]
import sys

from SocketTCP import SocketTCP

address = (sys.argv[1], int(sys.argv[2]))
SocketTCP.debug = "--debug" in sys.argv
if "--perdida" in sys.argv:
    SocketTCP.perdida = float(sys.argv[sys.argv.index("--perdida") + 1])
if "--timeout" in sys.argv:
    SocketTCP.timeout = float(sys.argv[sys.argv.index("--timeout") + 1])
mode = "go_back_n" if "--gbn" in sys.argv else "stop_and_wait"

server_socketTCP = SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()

# test 1
buff_size = 16
full_message = connection_socketTCP.recv(buff_size, mode=mode)
print("Test 1 received:", full_message)
if full_message == "Mensje de len=16".encode(): print("Test 1: Passed")
else: print("Test 1: Failed")

# test 2
buff_size = 19
full_message = connection_socketTCP.recv(buff_size, mode=mode)
print("Test 2 received:", full_message)
if full_message == "Mensaje de largo 19".encode(): print("Test 2: Passed")
else: print("Test 2: Failed")

# test 3
buff_size = 14
message_part_1 = connection_socketTCP.recv(buff_size, mode=mode)
message_part_2 = connection_socketTCP.recv(buff_size, mode=mode)
print("Test 3 received:", message_part_1 + message_part_2)
if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode(): print("Test 3: Passed")
else: print("Test 3: Failed")

# test 4: 2n bytes con n = 21, que no es multiplo de 16
buff_size = 21
message_part_1 = connection_socketTCP.recv(buff_size, mode=mode)
message_part_2 = connection_socketTCP.recv(buff_size, mode=mode)
print("Test 4 received:", message_part_1 + message_part_2)
if (message_part_1 + message_part_2) == ("a" * 21 + "b" * 21).encode(): print("Test 4: Passed")
else: print("Test 4: Failed")

# cierre de la conexion
connection_socketTCP.recv_close()
