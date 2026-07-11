import numpy as np

class KalmanPointTracker:
    """
    Kalman linear para um ponto 2D, modelo de velocidade constante
    """

    def __init__(self, x0, y0, capture_date, process_noise=4.0, measurement_noise=3.0):
        self.x = np.array([x0, y0, 0.0, 0.0], dtype=np.float64)
        self.P = np.eye(4) * 10.0
        self.q = process_noise
        self.r = measurement_noise
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float64)
        self.last_ts = capture_date
        self.missed_frames = 0

    def _F(self, dt):
        return np.array([[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1]], dtype=np.float64)

    def _Q(self, dt):
        q = self.q
        return np.array([
            [dt**4/4, 0, dt**3/2, 0],
            [0, dt**4/4, 0, dt**3/2],
            [dt**3/2, 0, dt**2, 0],
            [0, dt**3/2, 0, dt**2],
        ], dtype=np.float64) * q


    def step(self, z, capture_date, conf=1.0):
        dt = max(capture_date - self.last_ts, 1e-3)
        self.last_ts = capture_date

        F = self._F(dt)
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self._Q(dt)

        if z is not None:
            R = np.eye(2) * (self.r/max(conf,1e-3))
            y = z - self.H @ self.x
            S = self.H @ self.P @ self.H.T + R
            K = self.P @ self.H.T @ np.linalg.inv(S)
            self.x = self.x + K @ y
            self.P = (np.eye(4) - K @ self.H) @ self.P
            self.missed_frames = 0
        else:
            self.missed_frames += 1

        return self.x


_kalman_trackers: dict[tuple[int, int], KalmanPointTracker] = {}

# quais keypoints você realmente precisa suavizar (COCO: 0=nariz, 5/6=ombros, 11/12=quadris, 13/14=joelhos, 15/16=tornozelos)
TRACKED_KPTS = {0, 5, 6, 11, 12, 13, 14, 15, 16}
MAX_MISSED_FRAMES = 15  # limpa o tracker se sumir por N frames (evita leak de memória)
MIN_KPT_CONF = 0.3  # abaixo disso o keypoint é tratado como ausente (só predição)


def apply_kalman(person_id: int,capture_date: float, points: dict[int, list]) -> dict[int, dict]:
    """
    Recebe os keypoints brutos de uma pessoa nesse frame e retorna
    posição suavizada + velocidade para os pontos rastreados.
    """
    smoothed = {}

    for kpt_idx in TRACKED_KPTS:
        key = (person_id, kpt_idx)
        raw = points.get(kpt_idx)  
        valid = raw is not None and raw[2] >= MIN_KPT_CONF

        if key not in _kalman_trackers:
            if not valid:
                continue
            _kalman_trackers[key] = KalmanPointTracker(raw[0], raw[1], capture_date)

        z = np.array([raw[0], raw[1]]) if valid else None
        conf = raw[2] if valid else 0.0
        x, y, vx, vy = _kalman_trackers[key].step(z, capture_date, conf)
        smoothed[kpt_idx] = {"x": float(x), "y": float(y), "vx": float(vx), "vy": float(vy)}

    return smoothed

def cleanup_stale_trackers(active_person_ids: set[int]) -> None:
    """Remove trackers de pessoas que saíram de cena ou sumiram por muito tempo."""
    stale = [
        key for key, tracker in _kalman_trackers.items()
        if key[0] not in active_person_ids or tracker.missed_frames > MAX_MISSED_FRAMES
    ]
    for key in stale:
        del _kalman_trackers[key]
