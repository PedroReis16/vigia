"""Extração de features a partir dos resultados do YOLO para uso em LSTM/sequências."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from ultralytics.engine.results import Results

logger = logging.getLogger(__name__)


def extract_features_from_results(
    results: list[Results] | None,
    frame_width: int = 1,
    frame_height: int = 1,
    normalize: bool = True,
    max_detections: int | None = None,
) -> list[dict[str, Any]]:
    """Extrai features de detecção YOLO por objeto (centro x,y, bbox, confiança, classe).

    Útil para alimentar LSTM: uma sequência de frames, cada frame com N vetores de features.

    Args:
        results: Lista retornada por YOLODetector.predict (um resultado por frame).
        frame_width: Largura do frame (para normalizar coordenadas 0-1).
        frame_height: Altura do frame (para normalizar coordenadas 0-1).
        normalize: Se True, coordenadas são normalizadas em [0, 1].
        max_detections: Máximo de detecções por frame (útil para sequência fixa para LSTM).

    Returns:
        Lista de dicts, um por detecção, com chaves:
        - center_x, center_y: centro da bbox (normalizado ou em pixels)
        - width, height: largura e altura da bbox
        - conf: confiança da detecção
        - class_id: id da classe
        - class_name: nome da classe (se disponível)
        - frame_index: índice do frame (quando results tem múltiplos frames)
    """
    if not results:
        return []

    out: list[dict[str, Any]] = []
    for frame_idx, result in enumerate(results):
        if result.boxes is None or len(result.boxes) == 0:
            if max_detections is not None:
                for _ in range(max_detections):
                    out.append(_empty_detection(frame_idx, normalize))
            continue

        detections = []
        n_take = min(len(result.boxes), max_detections or len(result.boxes))
        for i in range(n_take):
            box = result.boxes[i]
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            width = x2 - x1
            height = y2 - y1

            if normalize and frame_width > 0 and frame_height > 0:
                center_x /= frame_width
                center_y /= frame_height
                width /= frame_width
                height /= frame_height

            conf = float(box.conf[0].item())
            cls = int(box.cls[0].item())
            class_name = result.names.get(cls, str(cls)) if hasattr(result, "names") else str(cls)

            detections.append({
                "center_x": center_x,
                "center_y": center_y,
                "width": width,
                "height": height,
                "conf": conf,
                "class_id": cls,
                "class_name": class_name,
                "frame_index": frame_idx,
            })
        out.extend(detections)

        if max_detections is not None and len(result.boxes) < max_detections:
            for _ in range(max_detections - len(result.boxes)):
                out.append(_empty_detection(frame_idx, normalize))
    return out


def _empty_detection(frame_index: int, normalize: bool) -> dict[str, Any]:
    """Placeholder para frame sem detecção (LSTM com sequência fixa)."""
    return {
        "center_x": 0.0,
        "center_y": 0.0,
        "width": 0.0,
        "height": 0.0,
        "conf": 0.0,
        "class_id": -1,
        "class_name": "",
        "frame_index": frame_index,
    }


def features_per_frame_to_sequence(
    features_list: list[list[dict[str, Any]]],
    keys: tuple[str, ...] = ("center_x", "center_y", "width", "height", "conf"),
    pick_best: bool = True,
) -> np.ndarray:
    """Converte lista de features por frame em array (n_frames, n_features) para LSTM.

    Se pick_best=True, usa apenas a detecção de maior confiança por frame.
    Caso contrário, concatena features de todas as detecções do frame (pode variar de tamanho).

    Args:
        features_list: Lista em que cada elemento é a lista de dicts de um frame
            (retornada por extract_features_from_results para um único frame).
        keys: Chaves dos dicts a incluir no vetor.
        pick_best: Se True, um vetor por frame (maior conf); se False, flatten por frame.

    Returns:
        Array numpy de shape (n_frames, n_features) se pick_best=True, ou
        (n_frames, n_detections * n_features) se pick_best=False (com padding se necessário).
    """
    if not features_list:
        return np.array([]).reshape(0, len(keys))

    n_features = len(keys)
    if pick_best:
        rows = []
        for frame_feats in features_list:
            if not frame_feats:
                rows.append([0.0] * n_features)
                continue
            best = max(frame_feats, key=lambda d: d.get("conf", 0))
            rows.append([float(best.get(k, 0)) for k in keys])
        return np.array(rows, dtype=np.float32)
    else:
        # Flatten all detections per frame (fixed size via max_detections antes)
        rows = []
        for frame_feats in features_list:
            row = []
            for d in frame_feats:
                row.extend([float(d.get(k, 0)) for k in keys])
            rows.append(row)
        # Pad to same length
        max_len = max(len(r) for r in rows)
        padded = []
        for r in rows:
            padded.append(r + [0.0] * (max_len - len(r)))
        return np.array(padded, dtype=np.float32)


def save_sequence_for_lstm(
    sequence: np.ndarray,
    path: str | Path,
    *,
    fmt: str = "npy",
) -> Path:
    """Salva sequência (n_frames, n_features) para uso posterior em LSTM.

    Args:
        sequence: Array (n_frames, n_features).
        path: Caminho base (sem extensão) ou com extensão.
        fmt: 'npy' (numpy) ou 'csv'.

    Returns:
        Caminho do arquivo salvo.
    """
    path = Path(path)
    if fmt == "npy":
        out_path = path if path.suffix == ".npy" else Path(str(path) + ".npy")
        np.save(out_path, sequence)
    elif fmt == "csv":
        out_path = path if path.suffix == ".csv" else Path(str(path) + ".csv")
        np.savetxt(out_path, sequence, delimiter=",", fmt="%.6f")
    else:
        raise ValueError(f"Formato não suportado: {fmt}")
    logger.info("Sequência salva: %s (%s)", out_path, sequence.shape)
    return out_path
