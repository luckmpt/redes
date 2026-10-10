# Tarea 4 - Parte 1: control de congestion estilo TCP Tahoe
# Solo maneja slow start y congestion avoidance (sin fast recovery)

SLOW_START = "slow_start"
CONGESTION_AVOIDANCE = "congestion_avoidance"


class CongestionControl:
    def __init__(self, MSS: int):
        self.MSS = MSS
        # la ventana parte siempre en 1 MSS
        self.cwnd = MSS
        # el umbral recien se define en el primer timeout
        self.ssthresh = None
        self.current_state = SLOW_START

    def get_cwnd(self):
        return self.cwnd

    def get_ssthresh(self):
        return self.ssthresh

    # cuantos MSS completos caben en la ventana
    def get_MSS_in_cwnd(self) -> int:
        return int(self.cwnd // self.MSS)

    def is_state_slow_start(self) -> bool:
        return self.current_state == SLOW_START

    def is_state_congestion_avoidance(self) -> bool:
        return self.current_state == CONGESTION_AVOIDANCE

    # si la ventana alcanza el umbral pasamos a congestion avoidance
    def check_state(self):
        if self.is_state_slow_start() and self.ssthresh is not None:
            if self.cwnd >= self.ssthresh:
                self.current_state = CONGESTION_AVOIDANCE

    def event_ack_received(self):
        if self.is_state_slow_start():
            # crecimiento exponencial: un MSS por cada ACK
            self.cwnd += self.MSS
        else:
            # AIMD: un MSS repartido entre todos los segmentos de la ventana
            self.cwnd += self.MSS / self.get_MSS_in_cwnd()
        self.check_state()

    def event_timeout(self):
        # multiplicative decrease: el umbral queda en la mitad de la ventana
        # va truncado a entero, porque se mide en bytes
        self.ssthresh = int(self.cwnd / 2)
        self.cwnd = self.MSS
        self.current_state = SLOW_START
        self.check_state()
