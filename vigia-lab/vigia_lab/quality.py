"""Métricas de qualidade de uma tomada e veredito (semáforo). Puro, sem I/O.

Entradas são arrays por FRAME PROCESSADO pelo YOLO (não só os entregues ao
classificador). O veredito diz à Ana se vale repetir a tomada.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Thresholds:
    fps_red: float = 8.0
    fps_yellow: float = 11.0
    delivered_yellow: float = 9.0    # GRUs foram treinados a 10 fps
    gap_red_s: float = 0.5          # lacuna sem tronco (maior)
    torso_valid_yellow: float = 0.80
    torso_valid_red: float = 0.50
    brightness_yellow: float = 60.0  # 0-255
    min_frames: int = 30
    video_drops_yellow: int = 1
    jitter_yellow_s: float = 0.15


def _longest_false_run_s(valid: np.ndarray, t: np.ndarray) -> float:
    """Maior intervalo de tempo contínuo em que `valid` é False."""
    best = 0.0
    start = None
    for i, ok in enumerate(valid):
        if not ok and start is None:
            start = i
        if ok and start is not None:
            best = max(best, t[i] - t[start])
            start = None
    if start is not None:
        best = max(best, t[-1] - t[start])
    return float(best)


def compute_quality(
    t_wall: np.ndarray,
    delivered: np.ndarray,
    yolo_ms: np.ndarray,
    torso_valid: np.ndarray,
    brightness: np.ndarray,
    n_tracks: int,
    mean_conf: float,
    camera_fps_nominal: float | None,
    video_drops: int = 0,
    event_window: tuple[float, float] | None = None,
) -> dict:
    """`event_window`: (t_ini, t_fim) em segundos relativos; a lacuna dentro dele pesa mais."""
    t = np.asarray(t_wall, dtype=np.float64)
    n = len(t)
    if n < 2:
        return {"n_frames": n, "pose_fps": 0.0, "n_tracks": n_tracks}
    t_rel = t - t[0]
    dt = np.diff(t)
    duration = float(t[-1] - t[0])
    torso = np.asarray(torso_valid, dtype=bool)
    q = {
        "n_frames": int(n),
        "duration_s": duration,
        "camera_fps_nominal": camera_fps_nominal,
        "pose_fps": float((n - 1) / duration) if duration > 0 else 0.0,
        "delivered_frames": int(np.sum(delivered)),
        "delivered_fps": float(np.sum(delivered) / duration) if duration > 0 else 0.0,
        "throttle_dropped": int(n - np.sum(delivered)),
        "yolo_ms_mean": float(np.mean(yolo_ms)),
        "yolo_ms_p95": float(np.percentile(yolo_ms, 95)),
        "dt_jitter_s": float(np.std(dt)),
        "dt_max_s": float(np.max(dt)),
        "torso_valid_frac": float(torso.mean()),
        "max_torso_gap_s": _longest_false_run_s(torso, t_rel),
        "n_tracks": int(n_tracks),
        "mean_conf": float(mean_conf),
        "brightness_mean": float(np.mean(brightness)),
        "video_drops": int(video_drops),
    }
    if event_window is not None:
        sel = (t_rel >= event_window[0]) & (t_rel <= event_window[1])
        q["max_torso_gap_in_event_s"] = (
            _longest_false_run_s(torso[sel], t_rel[sel]) if sel.sum() >= 2 else float("inf")
        )
    return q


def timing_summary(
    t_wall: np.ndarray, wait_ms: np.ndarray, yolo_ms: np.ndarray, consumer_ms: np.ndarray,
    cpu_pct: np.ndarray,
) -> dict:
    """Onde o tempo do laço foi gasto (para entender fps baixo).

    - wait_ms: tempo bloqueado esperando o resultado = câmera + YOLO + tracker + overhead do Ultralytics.
    - source_wait_ms = wait_ms - yolo_ms: espera pela câmera + custo do tracker/overhead (YOLO descontado).
    - consumer_ms: nosso processamento por frame (entrega aos modelos, janela, vídeo).
    - busy_frac: fração do intervalo entre frames ocupada por YOLO + nosso código.
    """
    if len(t_wall) < 3:
        return {}
    interval_ms = float(np.mean(np.diff(t_wall))) * 1000.0     # relógio da tomada (no replay é o do vídeo)
    dt_ms = float(np.mean(wait_ms + consumer_ms))              # tempo REAL do laço
    source_wait = np.maximum(wait_ms - yolo_ms, 0.0)
    busy = float(np.mean(yolo_ms + consumer_ms)) / dt_ms if dt_ms > 0 else 0.0
    wait_frac = float(np.mean(source_wait)) / dt_ms if dt_ms > 0 else 0.0
    if busy >= 0.8:
        bottleneck = "processamento (CPU)"
    elif wait_frac >= 0.4:
        bottleneck = "espera pela camera/tracker"
    else:
        bottleneck = "misto"
    return {
        "loop_dt_ms_mean": dt_ms,
        "frame_interval_ms_mean": interval_ms,
        "wait_ms_mean": float(np.mean(wait_ms)),
        "wait_ms_p95": float(np.percentile(wait_ms, 95)),
        "source_wait_ms_mean": float(np.mean(source_wait)),
        "consumer_ms_mean": float(np.mean(consumer_ms)),
        "consumer_ms_p95": float(np.percentile(consumer_ms, 95)),
        "busy_frac": busy,
        "source_wait_frac": wait_frac,
        "cpu_pct_mean": float(np.mean(cpu_pct)),
        "cpu_pct_max": float(np.max(cpu_pct)),
        "bottleneck": bottleneck,
    }


def verdict(q: dict, th: Thresholds = Thresholds()) -> tuple[str, list[str]]:
    """('verde'|'amarelo'|'vermelho', motivos)."""
    red: list[str] = []
    yellow: list[str] = []

    if q.get("n_frames", 0) < th.min_frames:
        red.append(f"poucos frames ({q.get('n_frames', 0)})")
        return "vermelho", red

    fps = q["pose_fps"]
    if fps < th.fps_red:
        red.append(f"fps do pose baixo ({fps:.1f})")
    elif fps < th.fps_yellow:
        yellow.append(f"fps do pose limítrofe ({fps:.1f})")

    if q["delivered_fps"] < th.delivered_yellow:
        yellow.append(f"poucos frames entregues aos modelos ({q['delivered_fps']:.1f}/s)")

    frac = q["torso_valid_frac"]
    if frac < th.torso_valid_red:
        red.append(f"tronco válido em só {frac:.0%} dos frames")
    elif frac < th.torso_valid_yellow:
        yellow.append(f"tronco válido em {frac:.0%} dos frames")

    gap_event = q.get("max_torso_gap_in_event_s")
    if gap_event is not None and gap_event > th.gap_red_s:
        red.append(f"tronco perdido por {gap_event:.1f}s durante o evento")
    elif q["max_torso_gap_s"] > th.gap_red_s:
        yellow.append(f"tronco perdido por {q['max_torso_gap_s']:.1f}s")

    if q["brightness_mean"] < th.brightness_yellow:
        yellow.append(f"imagem escura (brilho {q['brightness_mean']:.0f})")
    if q["video_drops"] >= th.video_drops_yellow:
        yellow.append(f"{q['video_drops']} frames de vídeo perdidos")
    if q["dt_jitter_s"] > th.jitter_yellow_s:
        yellow.append(f"intervalo entre frames irregular ({q['dt_jitter_s']:.2f}s)")
    if q.get("id_set_changes_delivered", 0) > 0:
        yellow.append(
            f"ID da pessoa mudou {q['id_set_changes_delivered']}x (historico dos modelos reiniciado)"
        )
    if q["n_tracks"] > 1:
        yellow.append(f"{q['n_tracks']} tracks (esperado 1 pessoa?)")

    if red:
        return "vermelho", red + yellow
    if yellow:
        return "amarelo", yellow
    return "verde", ["tomada dentro dos limites"]
