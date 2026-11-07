"""Qualidade da CAPTURA leve (sem pose) + veredito para a operadora.

Limiares (explicação, para defesa do PFC):
- fps medido < 20 vermelho, < 25 amarelo: a câmera nominal é 30 fps; a 15 fps o throttle do vigia
  (período >= 1/12 s) entregaria só 7,5 quadros/s e a janela dos modelos esticaria no tempo;
  a 20 fps ainda dá 10/s; abaixo disso a cadência de treino (10 fps) deixa de ser alcançável.
- frames perdidos > 0 amarelo, > 2% vermelho: cada perda é um buraco no vídeo.
- brilho < 60 (0-255) amarelo: pouca luz faz a webcam baixar a taxa e piora o YOLO.
- jitter (desvio do intervalo) > 15 ms amarelo.
- verificação de pose (pós-take): sem pessoa/tronco < 50% vermelho; < 80% amarelo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CaptureThresholds:
    fps_red: float = 20.0
    fps_yellow: float = 25.0
    drop_red_frac: float = 0.02
    brightness_yellow: float = 60.0
    jitter_yellow_s: float = 0.015
    torso_red: float = 0.50
    torso_yellow: float = 0.80
    min_frames: int = 30


def capture_metrics(
    t_mono: np.ndarray, brightness: np.ndarray, dropped: int, nominal_fps: float | None,
) -> dict:
    t = np.asarray(t_mono, dtype=np.float64)
    n = len(t)
    if n < 2:
        return {"n_frames": n, "measured_fps": 0.0, "dropped_frames": dropped, "camera_fps_nominal": nominal_fps}
    dt = np.diff(t)
    duration = float(t[-1] - t[0])
    return {
        "n_frames": int(n),
        "duration_s": duration,
        "measured_fps": float((n - 1) / duration) if duration > 0 else 0.0,
        "camera_fps_nominal": nominal_fps,
        "dt_max_s": float(dt.max()),
        "dt_jitter_s": float(dt.std()),
        "dropped_frames": int(dropped),
        "dropped_frac": float(dropped / (n + dropped)) if (n + dropped) else 0.0,
        "brightness_mean": float(np.mean(brightness)) if len(brightness) else 0.0,
    }


def capture_verdict(
    m: dict, pose_check: dict | None = None, th: CaptureThresholds = CaptureThresholds(),
) -> tuple[str, list[str]]:
    """('verde'|'amarelo'|'vermelho', motivos). `pose_check`: saída do quick_check (ou None)."""
    red: list[str] = []
    yellow: list[str] = []
    if m.get("n_frames", 0) < th.min_frames:
        return "vermelho", [f"poucos frames ({m.get('n_frames', 0)})"]

    fps = m["measured_fps"]
    if fps < th.fps_red:
        red.append(f"fps da camera baixo ({fps:.1f})")
    elif fps < th.fps_yellow:
        yellow.append(f"fps da camera limitrofe ({fps:.1f})")
    if m["dropped_frac"] > th.drop_red_frac:
        red.append(f"{m['dropped_frames']} frames perdidos")
    elif m["dropped_frames"] > 0:
        yellow.append(f"{m['dropped_frames']} frames perdidos")
    if m["brightness_mean"] < th.brightness_yellow:
        yellow.append(f"imagem escura (brilho {m['brightness_mean']:.0f})")
    if m["dt_jitter_s"] > th.jitter_yellow_s:
        yellow.append(f"intervalo entre frames irregular ({m['dt_jitter_s'] * 1000:.0f} ms)")

    if pose_check is not None:
        torso = pose_check.get("torso_valid_frac", 0.0)
        if pose_check.get("n_tracks", 0) == 0 or torso < th.torso_red:
            red.append(f"pessoa/tronco visivel em so {torso:.0%} dos frames amostrados")
        elif torso < th.torso_yellow:
            yellow.append(f"tronco visivel em {torso:.0%} dos frames amostrados")

    if red:
        return "vermelho", red + yellow
    if yellow:
        return "amarelo", yellow
    return "verde", ["captura dentro dos limites"]
