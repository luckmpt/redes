# Tarea 4 - Parte 1: control de congestion estilo TCP Tahoe
# Solo slow start y congestion avoidance, sin fast recovery

SLOW_START = "slow_start"
CONGESTION_AVOIDANCE = "congestion_avoidance"


class CongestionControl:
    def __init__(self, MSS: int):
        self.MSS = MSS
        # cwnd parte en 1 MSS
        self.cwnd = MSS
        # ssthresh recien se define en el primer timeout
        self.ssthresh = None
        self.current_state = SLOW_START

    def get_cwnd(self):
        return self.cwnd

    def get_ssthresh(self):
        return self.ssthresh

    # MSS completos que caben en cwnd
    def get_MSS_in_cwnd(self) -> int:
        return int(self.cwnd // self.MSS)

    def is_state_slow_start(self) -> bool:
        return self.current_state == SLOW_START

    def is_state_congestion_avoidance(self) -> bool:
        return self.current_state == CONGESTION_AVOIDANCE

    # cwnd >= ssthresh sale de slow start
    def check_state(self):
        if self.is_state_slow_start() and self.ssthresh is not None:
            if self.cwnd >= self.ssthresh:
                self.current_state = CONGESTION_AVOIDANCE

    def event_ack_received(self):
        if self.is_state_slow_start():
            # crecimiento exponencial, +1 MSS por ACK
            self.cwnd += self.MSS
        else:
            # additive increase, +1 MSS por ventana completa de ACKs
            self.cwnd += self.MSS / self.get_MSS_in_cwnd()
        self.check_state()

    def event_timeout(self):
        # multiplicative decrease, truncado porque cwnd va en bytes
        self.ssthresh = int(self.cwnd / 2)
        self.cwnd = self.MSS
        self.current_state = SLOW_START
        self.check_state()
