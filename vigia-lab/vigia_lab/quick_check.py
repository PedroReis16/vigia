"""Verificação rápida de pose DEPOIS da tomada (não durante, para não pesar na captura).

Roda o YOLO (mesmos kwargs do vigia, sem tracker) em 1 de cada `step` frames do vídeo recém-gravado:
~30 inferências por clipe de 10 s (~1 s no notebook). Responde: a pessoa apareceu? com o tronco visível?
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

TORSO = (5, 6, 11, 12)
MIN_KPT_CONF = 0.3          # igual a core.models.constants.MIN_KPT_CONF


def torso_visible(kp: np.ndarray) -> bool:
    """kp (17,3): os 4 pontos do tronco com confiança >= 0,3 (regra do point_filter do vigia)."""
    return bool((np.asarray(kp)[list(TORSO), 2] >= MIN_KPT_CONF).all())


def summarize_samples(persons_per_sample: list[list[np.ndarray]]) -> dict[str, Any]:
    """persons_per_sample: para cada frame amostrado, lista de keypoints (17,3) das pessoas."""
    n = len(persons_per_sample)
    if n == 0:
        return {"sampled": 0, "torso_valid_frac": 0.0, "n_tracks": 0}
    valid = [any(torso_visible(kp) for kp in people) for people in persons_per_sample]
    return {
        "sampled": n,
        "torso_valid_frac": float(np.mean(valid)),
        "n_tracks": max((sum(torso_visible(kp) for kp in people) for people in persons_per_sample), default=0),
    }


def run_quick_check(ctx: Any, video_path: Path, step: int = 10) -> dict[str, Any]:
    import time

    import cv2

    from vigia_lab import pose_source

    kwargs = {k: v for k, v in ctx.kwargs.items() if k not in ("stream", "persist", "tracker")}
    pose_source.reset_tracker(ctx.model)            # garante um predictor simples (sem rastreamento)
    samples: list[list[np.ndarray]] = []
    ms: list[float] = []
    cap = cv2.VideoCapture(str(video_path))
    try:
        i = -1
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            i += 1
            if i % step:
                continue
            t0 = time.perf_counter()
            res = ctx.model.predict(frame, **kwargs)[0]
            ms.append((time.perf_counter() - t0) * 1000.0)
            data = res.keypoints.data.cpu().numpy() if res.keypoints is not None and len(res.keypoints.data) else []
            samples.append([np.asarray(p) for p in data])
    finally:
        cap.release()
        pose_source.reset_tracker(ctx.model)        # o próximo uso (track) cria o predictor de rastreamento
    out = summarize_samples(samples)
    out["yolo_ms_mean"] = float(np.mean(ms)) if ms else 0.0
    return out
