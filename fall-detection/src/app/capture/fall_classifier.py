
import math
import warnings
import onnxruntime as ort
import numpy as np
import pandas as pd
from pathlib import Path

import joblib
from sklearn.exceptions import InconsistentVersionWarning

CONF_THRESHOLD = 0.3

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
    Wrapper completo: recebe keypoints brutos do YOLO e retorna
    a predição. É o único objeto que o colega precisa usar.
    """

    def __init__(self, model_path: str):
        self._session = ort.InferenceSession(model_path)
        self._input_name = self._session.get_inputs()[0].name

    def predict(self, keypoints_data: list) -> dict | None:
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

        pred  = int(self._session.run(None, {self._input_name: X})[0][0])
        # ONNX com SVM não exporta probabilidade por padrão
        # Para ter prob, use: convert_sklearn(..., options={"zipmap": False})
        # e acesse o segundo output
        proba_output = self._session.run(None, {self._input_name: X})
        prob = float(proba_output[1][0][1]) if len(proba_output) > 1 else float(pred)

        return {
            "label":        "deitado" if pred == 1 else "em_pe",
            "pred":         pred,
            "prob_deitado": prob,
        }