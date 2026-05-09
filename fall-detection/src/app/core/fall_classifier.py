from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort

# Alinhado ao _capture_frame em frame_consumer (keypoints com conf < 0.25 são zerados).
CONF_THRESHOLD = 0.25
NUM_KEYPOINTS = 17
FLAT_DIM = NUM_KEYPOINTS * 3  # x, y, conf por joint (COCO 17)

FEATURE_COLS = [
    "angle_from_vertical",
    "aspect_ratio",
    "trunk_ratio",
    "head_hip_ratio",
    "vert_alignment",
    "knee_angle",
]

def extract_features(keypoints_data: list) -> dict | None:
    joints = {
        kp["joint_id"]: kp
        for kp in keypoints_data
        if kp["conf"] > CONF_THRESHOLD
    }

    required = [5, 6, 11, 12]
    if not all(j in joints for j in required):
        return None

    ls, rs = joints[5], joints[6]
    lh, rh = joints[11], joints[12]

    sc = ((ls["x"] + rs["x"]) / 2, (ls["y"] + rs["y"]) / 2)
    hc = ((lh["x"] + rh["x"]) / 2, (lh["y"] + rh["y"]) / 2)

    dx = hc[0] - sc[0]
    dy = hc[1] - sc[1]

    raw_angle           = math.degrees(math.atan2(dy, dx))
    angle_from_vertical = abs(90 - abs(raw_angle))

    ys = [kp["y"] for kp in joints.values()]
    xs = [kp["x"] for kp in joints.values()]
    body_h       = max(ys) - min(ys)
    body_w       = max(xs) - min(xs)
    aspect_ratio = (body_w / body_h) if body_h > 1e-6 else 0.0

    trunk_len     = math.sqrt(dx**2 + dy**2)
    shoulder_w    = math.sqrt((ls["x"]-rs["x"])**2 + (ls["y"]-rs["y"])**2)
    hip_w         = math.sqrt((lh["x"]-rh["x"])**2 + (lh["y"]-rh["y"])**2)
    avg_lateral_w = (shoulder_w + hip_w) / 2 + 1e-6
    trunk_ratio   = trunk_len / avg_lateral_w

    trunk_height   = abs(sc[1] - hc[1]) + 1e-6
    head_hip_ratio = (hc[1] - joints[0]["y"]) / trunk_height if 0 in joints else float("nan")

    vert_alignment = dy / (trunk_len + 1e-6)

    knee_angle = float("nan")
    if all(j in joints for j in [11, 13, 15]):
        p1, p2, p3 = joints[11], joints[13], joints[15]
        v1 = (p1["x"]-p2["x"], p1["y"]-p2["y"])
        v2 = (p3["x"]-p2["x"], p3["y"]-p2["y"])
        cos_a = (v1[0]*v2[0] + v1[1]*v2[1]) / (
            (math.sqrt(v1[0]**2 + v1[1]**2) + 1e-6) *
            (math.sqrt(v2[0]**2 + v2[1]**2) + 1e-6)
        )
        knee_angle = math.degrees(math.acos(max(-1, min(1, cos_a))))

    return {
        "angle_from_vertical": angle_from_vertical,
        "aspect_ratio":        aspect_ratio,
        "trunk_ratio":         trunk_ratio,
        "head_hip_ratio":      head_hip_ratio,
        "vert_alignment":      vert_alignment,
        "knee_angle":          knee_angle,
    }


def _features_matrix_from_kpts_batch(k: np.ndarray) -> np.ndarray:
    """
    Mesmas features que extract_features, para todos os instantes de uma vez.

    k: (T, 17, 3) — x, y, conf por joint COCO.
    Retorna (T, 6); linha toda NaN se faltar ombro/quadil obrigatório (5,6,11,12).
    """
    t = k.shape[0]
    out = np.full((t, len(FEATURE_COLS)), np.nan, dtype=np.float64)

    conf_ok = k[:, :, 2] > CONF_THRESHOLD
    required_ok = conf_ok[:, 5] & conf_ok[:, 6] & conf_ok[:, 11] & conf_ok[:, 12]
    if not np.any(required_ok):
        return out

    ls_x, ls_y = k[:, 5, 0], k[:, 5, 1]
    rs_x, rs_y = k[:, 6, 0], k[:, 6, 1]
    lh_x, lh_y = k[:, 11, 0], k[:, 11, 1]
    rh_x, rh_y = k[:, 12, 0], k[:, 12, 1]

    sc_x = (ls_x + rs_x) * 0.5
    sc_y = (ls_y + rs_y) * 0.5
    hc_x = (lh_x + rh_x) * 0.5
    hc_y = (lh_y + rh_y) * 0.5

    dx = hc_x - sc_x
    dy = hc_y - sc_y
    raw_angle = np.degrees(np.arctan2(dy, dx))
    angle_from_vertical = np.abs(90.0 - np.abs(raw_angle))

    y_vis = np.where(conf_ok, k[:, :, 1], np.nan)
    x_vis = np.where(conf_ok, k[:, :, 0], np.nan)
    body_h = np.nanmax(y_vis, axis=1) - np.nanmin(y_vis, axis=1)
    body_w = np.nanmax(x_vis, axis=1) - np.nanmin(x_vis, axis=1)
    aspect_ratio = np.zeros(t, dtype=np.float64)
    np.divide(body_w, body_h, out=aspect_ratio, where=(body_h > 1e-6) & required_ok)

    trunk_len = np.hypot(dx, dy)
    shoulder_w = np.hypot(ls_x - rs_x, ls_y - rs_y)
    hip_w = np.hypot(lh_x - rh_x, lh_y - rh_y)
    avg_lateral_w = (shoulder_w + hip_w) * 0.5 + 1e-6
    trunk_ratio = trunk_len / avg_lateral_w

    trunk_height = np.abs(sc_y - hc_y) + 1e-6
    nose_ok = conf_ok[:, 0]
    head_hip_ratio = np.full(t, np.nan, dtype=np.float64)
    np.divide(hc_y - k[:, 0, 1], trunk_height, out=head_hip_ratio, where=nose_ok & required_ok)

    vert_alignment = np.divide(
        dy,
        trunk_len + 1e-6,
        out=np.zeros(t, dtype=np.float64),
        where=required_ok,
    )

    knee_ok = conf_ok[:, 11] & conf_ok[:, 13] & conf_ok[:, 15]
    p1 = k[:, 11, :2] - k[:, 13, :2]
    p2 = k[:, 15, :2] - k[:, 13, :2]
    dot = p1[:, 0] * p2[:, 0] + p1[:, 1] * p2[:, 1]
    n1 = np.linalg.norm(p1, axis=1) + 1e-6
    n2 = np.linalg.norm(p2, axis=1) + 1e-6
    cos_a = np.clip(dot / (n1 * n2), -1.0, 1.0)
    knee_angle = np.degrees(np.arccos(cos_a))
    knee_angle = np.where(knee_ok & required_ok, knee_angle, np.nan)

    idx_angle, idx_ar, idx_trunk, idx_head, idx_vert, idx_knee = range(6)
    out[:, idx_angle] = np.where(required_ok, angle_from_vertical, np.nan)
    out[:, idx_ar] = np.where(required_ok, aspect_ratio, np.nan)
    out[:, idx_trunk] = np.where(required_ok, trunk_ratio, np.nan)
    out[:, idx_head] = np.where(required_ok, head_hip_ratio, np.nan)
    out[:, idx_vert] = np.where(required_ok, vert_alignment, np.nan)
    out[:, idx_knee] = np.where(required_ok, knee_angle, np.nan)

    return out


def aggregate_window_features(window: np.ndarray) -> np.ndarray | None:
    """
    Agrega uma janela (T, 51) em um vetor de features (6,) via nanmean temporal,
    reduzindo ruído e custo (uma inferência ONNX por janela).

    Retorna None se não houver nenhum instante com ombros/quadis válidos.
    """
    w = np.asarray(window, dtype=np.float64)
    if w.ndim != 2 or w.shape[1] != FLAT_DIM:
        raise ValueError(f"janela esperada (T, {FLAT_DIM}), recebido {w.shape}")

    k = w.reshape(w.shape[0], NUM_KEYPOINTS, 3)
    feat_t = _features_matrix_from_kpts_batch(k)
    agg = np.nanmean(feat_t, axis=0)
    if np.all(np.isnan(agg)):
        return None
    return agg


def kpts_flat_to_keypoints_list(kpts_flat: np.ndarray) -> list[dict[str, Any]]:
    """
    Converte o vetor (51,) produzido pelo frame_consumer — 17 keypoints × (x, y, conf)
    em linha — para o formato de lista esperado por extract_features().
    """
    flat = np.asarray(kpts_flat, dtype=np.float64).reshape(-1)
    if flat.size != FLAT_DIM:
        raise ValueError(f"esperado vetor de tamanho {FLAT_DIM}, recebido {flat.size}")

    kpts = flat.reshape(NUM_KEYPOINTS, 3)
    return [
        {
            "joint_id": int(jid),
            "x": float(kpts[jid, 0]),
            "y": float(kpts[jid, 1]),
            "conf": float(kpts[jid, 2]),
        }
        for jid in range(NUM_KEYPOINTS)
    ]


def build_keypoints_list(kps_array, kconf_array, person_idx: int = 0) -> list:
    """
    Converte a saída bruta do YOLO (arrays NumPy) para o formato
    que extract_features() espera.

    kps_array  : resultado de model(frame)[0].keypoints.xy.cpu().numpy()
                 shape (N_pessoas, 17, 2)
    kconf_array: resultado de model(frame)[0].keypoints.conf.cpu().numpy()
                 shape (N_pessoas, 17)
    person_idx : índice da pessoa a classificar (default: 0, a principal)
    """
    return [
        {
            "joint_id": jid,
            "x":        float(kps_array[person_idx, jid, 0]),
            "y":        float(kps_array[person_idx, jid, 1]),
            "conf":     float(kconf_array[person_idx, jid]),
        }
        for jid in range(kps_array.shape[1])
    ]


class FallClassifier:
    """
    Classificador de queda: lista de joints, vetor (51,) ou janela (T, 51).
    Janelas são agregadas em NumPy (uma passagem ONNX por janela).
    """

    def __init__(self):
        self._session = ort.InferenceSession(Path(__file__).resolve().parents[3]/"model"/"classifier_svm.onnx")
        self._input_name = self._session.get_inputs()[0].name

    def predict(self, keypoints_data: list | np.ndarray) -> dict | None:
        if isinstance(keypoints_data, np.ndarray):
            arr = np.asarray(keypoints_data, dtype=np.float64)
            if arr.ndim == 2 and arr.shape[1] == FLAT_DIM:
                vec = aggregate_window_features(arr)
                if vec is None:
                    return None
                X = np.asarray(vec, dtype=np.float32).reshape(1, -1)
            elif arr.ndim == 1 and arr.size == FLAT_DIM:
                feats = extract_features(kpts_flat_to_keypoints_list(arr))
                if feats is None:
                    return None
                X = np.array([[
                    feats.get("angle_from_vertical", 0),
                    feats.get("aspect_ratio", 0),
                    feats.get("trunk_ratio", 0),
                    feats.get("head_hip_ratio", 0),
                    feats.get("vert_alignment", 0),
                    feats.get("knee_angle", 0),
                ]], dtype=np.float32)
            else:
                raise ValueError(
                    f"array deve ser (T, {FLAT_DIM}) ou ({FLAT_DIM},), recebido {arr.shape}"
                )
        else:
            feats = extract_features(keypoints_data)
            if feats is None:
                return None
            X = np.array([[
                feats.get("angle_from_vertical", 0),
                feats.get("aspect_ratio", 0),
                feats.get("trunk_ratio", 0),
                feats.get("head_hip_ratio", 0),
                feats.get("vert_alignment", 0),
                feats.get("knee_angle", 0),
            ]], dtype=np.float32)

        # NaN vira 0 (mesmo comportamento do SimpleImputer com median≈0)
        X = np.nan_to_num(X, nan=0.0)

        outputs = self._session.run(None, {self._input_name: X})
        pred = int(outputs[0][0])
        # ONNX com SVM não exporta probabilidade por padrão
        # Para ter prob, use: convert_sklearn(..., options={"zipmap": False})
        # e acesse o segundo output
        prob = float(outputs[1][0][1]) if len(outputs) > 1 else float(pred)

        return {
            "label":        "deitado" if pred == 1 else "em_pe",
            "pred":         pred,
            "prob_deitado": prob,
        }