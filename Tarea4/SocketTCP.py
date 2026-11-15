import random as rd
import socket
import time

from CongestionControl import CongestionControl
from slidingWindowCC import SlidingWindowCC
from socketUDP import SocketUDP

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
        # control de congestion para go back n, MSS de 8 bytes
        self.congestion_controler = CongestionControl(8)
        self.congestion_control_on = False
        self.number_of_sent_segments = 0

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

    def send_using_stop_and_wait(self, message: bytes):
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
            # perdida a mano al llegar, asi tambien se pierden los datos de go back n
            if rd.random() < SocketTCP.perdida:
                self.log(f"(perdido al llegar) {msg}")
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

    def recv_using_stop_and_wait(self, buff_size: int):
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

    def send(self, message, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            self.send_using_go_back_n(message)

    def recv(self, buff_size, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

    def set_congestion_control(self, valor: bool):
        self.congestion_control_on = valor

    # el receptor de go back n es el mismo de stop & wait: acepta solo en orden
    # y lo demas lo descarta reenviando el ultimo ACK
    def recv_using_go_back_n(self, buff_size: int):
        return self.recv_using_stop_and_wait(buff_size)

    # cambia el tamaño de la ventana segun la cwnd
    def actualizar_ventana(self, data_window):
        cc = self.congestion_controler
        window_size = cc.get_MSS_in_cwnd()
        data_window.update_window_size(window_size)
        self.log(f"cwnd={cc.get_cwnd()} ssthresh={cc.get_ssthresh()} estado={cc.current_state} window_size={window_size}")

    # manda los elementos de la ventana desde 'desde' en adelante, retorna cuantos van mandados
    def enviar_ventana(self, data_window, timer, desde):
        i = desde
        while i < data_window.window_size and data_window.get_data(i) is not None:
            current_seq = data_window.get_sequence_number(i)
            current_data = data_window.get_data(i)
            self.log(f"envia {current_data} seq={current_seq}")
            timer.sendto(self.armar(current_seq, message=current_data), self.direccion, timer_index=0)
            self.number_of_sent_segments += 1
            i += 1
        return i

    # pasa el seq del ACK (4 digitos) a numero completo, usando el inicio de la ventana
    def ack_completo(self, data_window, seq):
        inicio = data_window.get_sequence_number(0)
        distancia = (int(seq) - inicio) % 10000
        if distancia > 5000:  # ACK atrasado de algo ya confirmado
            return inicio
        return inicio + distancia

    def send_using_go_back_n(self, message: bytes):
        message_length = str(len(message)).encode()
        # dividimos el mensaje en trozos de MSS = 8 bytes
        data_list = [message[i:i + 8] for i in range(0, len(message), 8)]

        if self.congestion_control_on:
            window_size = self.congestion_controler.get_MSS_in_cwnd()
        else:
            window_size = 8
        data_window = SlidingWindowCC(window_size, [message_length] + data_list, self.secNum)
        if self.congestion_control_on:
            self.actualizar_ventana(data_window)

        # SocketUDP sobre nuestro socket, para manejar el timer a mano
        timer = SocketUDP()
        timer.socket_udp = self.socketUDP
        self.socketUDP.setblocking(False)
        timer.settimeout(self.timeout)

        # partimos mandando toda la ventana
        enviados = self.enviar_ventana(data_window, timer, 0)

        while data_window.get_data(0) is not None:
            try:
                answer, address = timer.recvfrom(BUFF_UDP)
            except TimeoutError:
                # go back n: se reenvia toda la ventana
                self.log(f"timeout, se reenvia la ventana desde seq={data_window.get_sequence_number(0)}")
                timer.stop_timer(timer_index=0)
                if self.congestion_control_on:
                    self.congestion_controler.event_timeout()
                    self.actualizar_ventana(data_window)
                enviados = self.enviar_ventana(data_window, timer, 0)
                continue

            ack = self.parseSegment(answer)
            # caso borde de la tarea 3: el servidor no recibio el ACK del handshake
            if ack["SYN"] and ack["ACK"] and self.ackHandshake is not None:
                self.enviar(self.ackHandshake, self.direccion)
                continue
            if not ack["ACK"] or ack["SYN"] or ack["FIN"]:
                continue

            # el ACK es acumulativo: movemos la ventana por cada elemento que confirma.
            # Si la ventana se achico, el ACK puede ser de algo que quedo afuera (caso borde),
            # asi que se sigue moviendo hasta que el ACK caiga dentro
            ack_seq = self.ack_completo(data_window, ack["seq"])
            avanzo = False
            while data_window.get_data(0) is not None and \
                    data_window.get_sequence_number(0) + len(data_window.get_data(0)) <= ack_seq:
                self.secNum = data_window.get_sequence_number(0) + len(data_window.get_data(0))
                data_window.move_window(1)
                enviados = max(0, enviados - 1)
                avanzo = True
            if not avanzo:
                continue  # ACK repetido

            if self.congestion_control_on:
                self.congestion_controler.event_ack_received()
                self.actualizar_ventana(data_window)

            # el timer se reinicia si entra algo nuevo a la ventana;
            # si no, sigue corriendo por los que faltan confirmar
            hay_nuevo = enviados < data_window.window_size and data_window.get_data(enviados) is not None
            if data_window.get_data(0) is None or hay_nuevo:
                timer.stop_timer(timer_index=0)
            enviados = self.enviar_ventana(data_window, timer, enviados)

        # el socket vuelve a modo normal para close y stop & wait
        self.socketUDP.settimeout(self.timeout)

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
