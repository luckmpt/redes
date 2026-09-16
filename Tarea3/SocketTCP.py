import socket
import random as rd

class SocketTCP:
    def __init__(self):
        self.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.direccion = (None, None)
        self.secNum = None
        self.por_recibir = 0
        self.sobrante = b""

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

    def bind(self, addres: str):
        self.direccion = addres
        self.socketUDP.bind(addres)

    def connect(self, addres: str):
        self.direccion = addres
        self.secNum = rd.randint(0, 1000)
        msj1 = self.createSegment({
            "ACK": False,
            "SYN": True,
            "FIN": False,
            "seq": str(self.secNum).zfill(4).encode(),
            "message": b""
        })
        self.socketUDP.sendto(msj1, addres)
        resp, addr = self.socketUDP.recvfrom(7)
        parse_recv = self.parseSegment(resp)
        if parse_recv["SYN"] and parse_recv["ACK"] and parse_recv["seq"] == str(self.secNum + 1).zfill(4).encode():
            self.secNum += 2
            msj2 = self.createSegment({
                "ACK": True,
                "SYN": False,
                "FIN": False,
                "seq": str(self.secNum).zfill(4).encode(),
                "message": b""
            })
            self.direccion = addr
            self.socketUDP.sendto(msj2, self.direccion)
            print(f"direccion del servidor: {self.direccion[0]}:{self.direccion[1]}")

    def accept(self):
        msg, addr = self.socketUDP.recvfrom(7)
        parse_recv = self.parseSegment(msg)
        if parse_recv["SYN"]:
            secNum = int(parse_recv["seq"]) + 1
            msj1 = self.createSegment({
                "ACK": True,
                "SYN": True,
                "FIN": False,
                "seq": str(secNum).zfill(4).encode(),
                "message": b""
            })
            newSocket = SocketTCP()
            newSocket.direccion = (self.direccion[0], self.direccion[1]+1)
            newSocket.bind(newSocket.direccion)
            newSocket.socketUDP.sendto(msj1, addr)
            resp, _ = newSocket.socketUDP.recvfrom(7)
            parse_recv2 = newSocket.parseSegment(resp)
            if parse_recv2["ACK"] and parse_recv2["seq"] == str(secNum + 1).zfill(4).encode():
                self.secNum = secNum+1
                newSocket.socketUDP.settimeout(5)
                newSocket.secNum = secNum
                print("fin de handshake, se conectan servidor y cliente")
                print(f"direccion del servidor: {newSocket.direccion[0]}:{newSocket.direccion[1]}")
                return newSocket, newSocket.direccion

    def send(self, message: bytes):
        message_lenght = len(message)
        lenght_bytes = str(message_lenght).encode()
        lenght_lenght = len(lenght_bytes)
        msjInit = self.createSegment({
            "ACK": False,
            "SYN": False,
            "FIN": False,
            "seq": str(self.secNum).zfill(4).encode(),
            "message": lenght_bytes
        })
        b = False
        while not b:
            print(f"envia largo: {msjInit} y seq={self.secNum}")
            self.socketUDP.sendto(msjInit, self.direccion)
            respInit, _ = self.socketUDP.recvfrom(7)
            parse_recvInit = self.parseSegment(respInit)
            print(f"recibe {parse_recvInit}")
            if parse_recvInit["ACK"] and parse_recvInit["seq"] == str(self.secNum + lenght_lenght).zfill(4).encode():
                b = True
                self.secNum += lenght_lenght
        i = 0
        while i < message_lenght:
            if i + 16 < message_lenght:
                msg = message[i:i+16]
            else:
                msg = message[i:message_lenght]
            msj1 = self.createSegment({
                "ACK": False,
                "SYN": False,
                "FIN": False,
                "seq": str(self.secNum).zfill(4).encode(),
                "message": msg
            })
            print(f"envia {msg} y seq={self.secNum}")
            self.socketUDP.sendto(msj1, self.direccion)
            resp, _ = self.socketUDP.recvfrom(7)
            parse_recv = self.parseSegment(resp)
            print(f"recibe {parse_recv}")
            len_msg = len(msg)
            if parse_recv["ACK"] and parse_recv["seq"] == str(self.secNum + len_msg).zfill(4).encode():
                self.secNum += len_msg
                i += len_msg

    def recv(self, buff_size: int):
        if self.por_recibir == 0:
            msgInit, addr = self.socketUDP.recvfrom(7+16)
            parse_recvInit = self.parseSegment(msgInit)
            print(f"recibe {parse_recvInit}")
            lenght_lenght = len(parse_recvInit["message"])
            lenght_full_message = int(parse_recvInit["message"])
            self.por_recibir = lenght_full_message
            self.direccion = addr
            self.secNum = int(parse_recvInit["seq"]) + lenght_lenght
            msjInit = self.createSegment({
                "ACK": True,
                "SYN": False,
                "FIN": False,
                "seq": str(self.secNum).zfill(4).encode(),
                "message": b""
            })
            print(f"envia ACK y seq = {self.secNum}")
            self.socketUDP.sendto(msjInit, self.direccion)
        buff = self.sobrante
        self.sobrante = b""
        seq = None
        while len(buff) < min(self.por_recibir, buff_size):
            msg, addr = self.socketUDP.recvfrom(7+16)
            parse_recv = self.parseSegment(msg)
            print(f"recibe {parse_recv}")
            seq = parse_recv["seq"]
            msg_recib = parse_recv["message"]
            self.secNum = int(seq) + len(msg_recib)
            if len(buff) + len(msg_recib) > buff_size:
                msg_recib = msg_recib[:buff_size-len(buff)]
                self.sobrante = msg_recib[len(buff):]
            buff += msg_recib
            msj1 = self.createSegment({
                "ACK": True,
                "SYN": False,
                "FIN": False,
                "seq": str(self.secNum).zfill(4).encode(),
                "message": b""
            })
            print(f"envia ACK y seq = {self.secNum}")
            self.socketUDP.sendto(msj1, self.direccion)
        self.por_recibir -= len(buff)
        print(f"recibido {len(buff)} bytes")
        return buff
