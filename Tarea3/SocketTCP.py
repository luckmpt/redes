import random as rd
import socket
import time

HEADER = 7  # ACK + SYN + FIN + seq de 4 digitos
MSS = 16  # datos maximos por segmento
BUFF_UDP = HEADER + MSS


class SocketTCP:
    # compartidos por todos los sockets, se cambian desde cliente/servidor
    debug = False
    perdida = 0.0  # probabilidad de perder un segmento al enviarlo (perdida a mano)
    timeout = 2.0  # segundos, tiene que ser mayor al RTT

    def __init__(self):
        self.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.direccion = (None, None)
        self.secNum = None
        self.por_recibir = 0
        self.sobrante = b""
        # ultimo ACK del handshake, se reenvia si el servidor no lo recibio
        self.ackHandshake = None

    def log(self, texto):
        if SocketTCP.debug:
            print(f"(debug) {texto}")

    @staticmethod
    def parseSegment(segment: bytes):
        ACK = bool(int(segment[0:1]))
        SYN = bool(int(segment[1:2]))
        FIN = bool(int(segment[2:3]))
        seq = segment[3:7]
        if len(segment) > 7:
            message = segment[7:]
        else:
            message = b""
        return {
            "ACK": ACK,
            "SYN": SYN,
            "FIN": FIN,
            "seq": seq,
            "message": message
        }

    @staticmethod
    def createSegment(parse: dict):
        SYN = b"0"
        FIN = b"0"
        ACK = b"0"
        if parse["ACK"]:
            ACK = b"1"
        if parse["SYN"]:
            SYN = b"1"
        if parse["FIN"]:
            FIN = b"1"
        seq = parse["seq"]
        message = parse["message"] if "message" in parse else b""
        return ACK+SYN+FIN+seq+message

    # el seq va en 4 digitos, asi que da la vuelta en 10000 para no romper el header
    @staticmethod
    def seqBytes(n):
        return str(n % 10000).zfill(4).encode()

    @staticmethod
    def mismoSeq(campo, n):
        return int(campo) == n % 10000

    @staticmethod
    def esDato(p):
        return not p["ACK"] and not p["SYN"] and not p["FIN"]

    def armar(self, seq, ACK=False, SYN=False, FIN=False, message=b""):
        return self.createSegment({
            "ACK": ACK,
            "SYN": SYN,
            "FIN": FIN,
            "seq": self.seqBytes(seq),
            "message": message
        })

    # sendto con perdida simulada, para probar sin netem
    def enviar(self, segmento, direccion):
        if rd.random() < SocketTCP.perdida:
            self.log(f"(perdido) {segmento}")
            return
        self.socketUDP.sendto(segmento, direccion)

    def bind(self, addres: str):
        self.direccion = addres
        self.socketUDP.bind(addres)

    def connect(self, addres: str):
        self.secNum = rd.randint(0, 100)
        syn = self.armar(self.secNum, SYN=True)
        self.socketUDP.settimeout(self.timeout)
        # stop & wait: se reenvia el SYN hasta que llegue el SYN+ACK
        while True:
            self.log(f"envia SYN seq={self.secNum}")
            self.enviar(syn, addres)
            try:
                resp, addr = self.socketUDP.recvfrom(BUFF_UDP)
            except socket.timeout:
                self.log("timeout esperando SYN+ACK, se reenvia SYN")
                continue
            p = self.parseSegment(resp)
            if p["SYN"] and p["ACK"] and self.mismoSeq(p["seq"], self.secNum + 1):
                break
        # el SYN+ACK viene del socket nuevo que creo accept, desde ahi se sigue
        self.direccion = addr
        self.secNum += 2
        self.ackHandshake = self.armar(self.secNum, ACK=True)
        self.log(f"envia ACK seq={self.secNum}, conectado a {addr}")
        self.enviar(self.ackHandshake, self.direccion)

    def accept(self):
        # el socket que escucha espera sin timeout hasta que llegue un SYN
        while True:
            msg, addr = self.socketUDP.recvfrom(BUFF_UDP)
            p = self.parseSegment(msg)
            if p["SYN"] and not p["ACK"]:
                break
        x = int(p["seq"])
        nuevo = SocketTCP()
        # puerto 0: el SO elige uno libre, distinto al del socket que escucha
        nuevo.bind((self.direccion[0], 0))
        nuevo.direccion = addr
        nuevo.socketUDP.settimeout(nuevo.timeout)
        synack = nuevo.armar(x + 1, SYN=True, ACK=True)
        while True:
            nuevo.log(f"envia SYN+ACK seq={x + 1}")
            nuevo.enviar(synack, addr)
            try:
                resp, _ = nuevo.socketUDP.recvfrom(BUFF_UDP)
            except socket.timeout:
                nuevo.log("timeout esperando ACK, se reenvia SYN+ACK")
                continue
            p = nuevo.parseSegment(resp)
            if p["ACK"] and not p["SYN"] and nuevo.mismoSeq(p["seq"], x + 2):
                break
            # caso borde: se perdio el ACK pero el cliente ya esta mandando datos con seq x+2,
            # eso confirma el handshake. El dato se descarta y el cliente lo reenvia por timeout
            if nuevo.esDato(p) and nuevo.mismoSeq(p["seq"], x + 2):
                nuevo.log("llega un dato en vez del ACK, se toma como ACK implicito")
                break
        nuevo.secNum = x + 2
        nuevo.log(f"handshake listo, conexion en {nuevo.socketUDP.getsockname()}")
        return nuevo, nuevo.socketUDP.getsockname()

    # espera el ACK con el seq esperado, False si se cumple el timeout
    def esperarAck(self, esperado):
        try:
            while True:
                resp, _ = self.socketUDP.recvfrom(BUFF_UDP)
                p = self.parseSegment(resp)
                if p["ACK"] and not p["SYN"] and not p["FIN"] and self.mismoSeq(p["seq"], esperado):
                    return True
                # caso borde: el servidor no recibio el ACK del handshake y reenvio el SYN+ACK
                if p["SYN"] and p["ACK"] and self.ackHandshake is not None:
                    self.log("llega SYN+ACK repetido, se reenvia el ACK del handshake")
                    self.enviar(self.ackHandshake, self.direccion)
                # cualquier otra cosa es un ACK atrasado y se ignora
        except socket.timeout:
            return False

    def send(self, message: bytes):
        # el primer segmento lleva el largo, despues el mensaje en trozos de MSS
        largo = str(len(message)).encode()
        trozos = [largo] + [message[i:i + MSS] for i in range(0, len(message), MSS)]
        self.socketUDP.settimeout(self.timeout)
        for trozo in trozos:
            seg = self.armar(self.secNum, message=trozo)
            esperado = self.secNum + len(trozo)
            while True:
                self.log(f"envia {trozo} seq={self.secNum}")
                self.enviar(seg, self.direccion)
                if self.esperarAck(esperado):
                    break
                self.log(f"timeout, se reenvia seq={self.secNum}")
            self.secNum = esperado

    # recibe el siguiente segmento en orden, le manda su ACK y devuelve los datos
    def recibirSegmento(self):
        while True:
            try:
                msg, _ = self.socketUDP.recvfrom(BUFF_UDP)
            except socket.timeout:
                continue
            p = self.parseSegment(msg)
            if not self.esDato(p):
                continue
            if self.mismoSeq(p["seq"], self.secNum):
                self.secNum += len(p["message"])
                self.log(f"recibe {p['message']}, envia ACK seq={self.secNum}")
                self.enviar(self.armar(self.secNum, ACK=True), self.direccion)
                return p["message"]
            # segmento repetido: se perdio nuestro ACK, se reenvia el ultimo
            self.log(f"llega seq={int(p['seq'])} repetido, se reenvia ACK seq={self.secNum}")
            self.enviar(self.armar(self.secNum, ACK=True), self.direccion)

    def recv(self, buff_size: int):
        # lo que sobro del recv anterior va primero, sin pasarse de buff_size
        buff = self.sobrante[:buff_size]
        self.sobrante = self.sobrante[buff_size:]
        if self.por_recibir == 0:
            # mensaje nuevo: el primer segmento trae el largo
            self.por_recibir = int(self.recibirSegmento())
            self.log(f"largo del mensaje: {self.por_recibir}")
        while len(buff) < min(self.por_recibir, buff_size):
            datos = self.recibirSegmento()
            falta = buff_size - len(buff)
            buff += datos[:falta]
            # lo que no cabe se guarda para el proximo recv
            self.sobrante += datos[falta:]
        self.por_recibir -= len(buff)
        return buff

    def close(self):
        fin = self.armar(self.secNum, FIN=True)
        self.socketUDP.settimeout(self.timeout)
        recibido = False
        # se reenvia el FIN hasta 3 timeouts
        for intento in range(3):
            self.log(f"envia FIN seq={self.secNum}")
            self.enviar(fin, self.direccion)
            try:
                while True:
                    resp, _ = self.socketUDP.recvfrom(BUFF_UDP)
                    p = self.parseSegment(resp)
                    if p["FIN"] and p["ACK"] and self.mismoSeq(p["seq"], self.secNum + 1):
                        recibido = True
                        break
            except socket.timeout:
                self.log(f"timeout {intento + 1}/3 esperando FIN+ACK")
            if recibido:
                break
        if recibido:
            self.secNum += 2
            ack = self.armar(self.secNum, ACK=True)
            # el ultimo ACK va 3 veces por si se pierde, con un timeout entre medio
            for i in range(3):
                self.log(f"envia ACK final seq={self.secNum} ({i + 1}/3)")
                self.enviar(ack, self.direccion)
                if i < 2:
                    time.sleep(self.timeout)
        else:
            self.log("3 timeouts sin FIN+ACK, se asume que el otro lado cerro")
        self.socketUDP.close()
        self.log("conexion cerrada")

    def recv_close(self):
        # espera el FIN; un dato repetido significa que se perdio nuestro ultimo ACK
        while True:
            try:
                msg, _ = self.socketUDP.recvfrom(BUFF_UDP)
            except socket.timeout:
                continue
            p = self.parseSegment(msg)
            if p["FIN"] and not p["ACK"]:
                break
            if self.esDato(p):
                self.log(f"dato repetido antes del FIN, se reenvia ACK seq={self.secNum}")
                self.enviar(self.armar(self.secNum, ACK=True), self.direccion)
        self.secNum = int(p["seq"]) + 1
        finack = self.armar(self.secNum, FIN=True, ACK=True)
        timeouts = 0
        while timeouts < 3:
            self.log(f"envia FIN+ACK seq={self.secNum}")
            self.enviar(finack, self.direccion)
            try:
                while True:
                    resp, _ = self.socketUDP.recvfrom(BUFF_UDP)
                    p = self.parseSegment(resp)
                    if p["ACK"] and not p["FIN"] and self.mismoSeq(p["seq"], self.secNum + 1):
                        self.socketUDP.close()
                        self.log("llega el ACK final, conexion cerrada")
                        return
                    # se perdio el FIN+ACK y el otro lado reenvio su FIN
                    if p["FIN"]:
                        break
            except socket.timeout:
                timeouts += 1
                self.log(f"timeout {timeouts}/3 esperando el ACK final")
        self.socketUDP.close()
        self.log("3 timeouts sin ACK final, se asume que el otro lado cerro")
