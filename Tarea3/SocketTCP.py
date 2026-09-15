import socket
import random as rd

class SocketTCP:
    def __init__(self):
        self.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ipDestino = None
        self.portDestino = None
        self.secNum = None

    @staticmethod
    def parseSegment(segment: bytes):
        ACK = bool(int(segment[0:1]))
        SYN = bool(int(segment[1:2]))
        FIN = bool(int(segment[2:3]))
        seq = segment[3:]
        return {
            "ACK": ACK,
            "SYN": SYN,
            "FIN": FIN,
            "seq": seq
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
        return ACK+SYN+FIN+seq
    
    def bind(self, addres: str):
        self.socketUDP.bind(addres)

    def connect(self, addres: str):
        self.ipDestino = addres[0]
        self.portDestino = addres[1]
        self.secNum = rd.randint(0, 1000)
        msj1 = self.createSegment({
            "ACK": False,
            "SYN": True,
            "FIN": False,
            "seq": str(self.secNum).encode()
        })
        self.socketUDP.sendto(msj1, addres)
        resp, _ = self.socketUDP.recvfrom(16)
        parse_recv = self.parseSegment(resp)
        if parse_recv["SYN"] and parse_recv["ACK"] and parse_recv["seq"] == str(self.secNum + 1).encode():
            print(f"recibe {parse_recv}")
            self.secNum += 2
            msj2 = self.createSegment({
                "ACK": True,
                "SYN": False,
                "FIN": False,
                "seq": str(self.secNum).encode()
            })
            self.socketUDP.sendto(msj2, addres)
        self.socketUDP.close()

    def accept(self):
        msg, addr = self.socketUDP.recvfrom(16)
        parse_recv = self.parseSegment(msg)
        if parse_recv["SYN"]:
            ipDestino = addr[0]
            portDestino = addr[1]
            secNum = int(parse_recv["seq"]) + 1
            msj1 = self.createSegment({
                "ACK": True,
                "SYN": True,
                "FIN": False,
                "seq": str(secNum).encode()
            })
            print("enviar ACK, SYN, seq+1")
            self.socketUDP.sendto(msj1, addr)
            resp, _ = self.socketUDP.recvfrom(16)
            parse_recv2 = self.parseSegment(resp)
            if parse_recv2["ACK"] and parse_recv2["seq"] == str(secNum + 1).encode():
                self.secNum = secNum+1
                newSocket = SocketTCP()
                newSocket.ipDestino = ipDestino
                newSocket.portDestino = portDestino
                newSocket.secNum = secNum
                self.socketUDP.close()
                newSocket.bind(addr)
                return newSocket, addr