"""
Processa os frames capturados para inclusão na fila de processamento
"""

from math import dist
from typing import Any
import numpy as np

from capture.models import (
    align_and_store_pca_angle,
    get_smoothed_scale,
    get_yolo_model,
    apply_kalman,
    cleanup_stale_trackers,
    get_trunk_angle,
    get_pca_features,
)


def __get_central_point(point_left: float, point_right: float) -> float:
    """
    Obtém o ponto central entre dois pontos
    """
    return (point_left + point_right) / 2


def __normalize_body_part(
    scale: float, hip: tuple[float, float], body_part: tuple[float, float]
) -> tuple[float, float]:
    """
    Normaliza a parte do corpo em relação a posição centralizada do quadril, mantendo a escala do torso
    """
    x = (body_part["x"] - hip[0]) / scale
    y = (body_part["y"] - hip[1]) / scale

    return x, y


def __normalize_data(
    frame_points: dict[int, list[float]],
) -> dict[int, dict[int, tuple[float, float]]]:
    """
    Normaliza os dados dos keypoints para o tamanho da imagem
    """

    normalized_data = {}

    for person_id, (_, smoothed_points) in frame_points.items():
        # Normalizando o torso do corpo

        shoulder_left = smoothed_points.get(5, None)
        shoulder_right = smoothed_points.get(6, None)
        hip_left = smoothed_points.get(11, None)
        hip_right = smoothed_points.get(12, None)

        # Se os pontos de ombro ou quadril não forem encontrados, pula o cálculo
        if (
            shoulder_left is None
            or shoulder_right is None
            or hip_left is None
            or hip_right is None
        ):
            continue

        shoulder_center = (
            __get_central_point(shoulder_left["x"], shoulder_right["x"]),
            __get_central_point(shoulder_left["y"], shoulder_right["y"]),
        )
        hip_center = (
            __get_central_point(hip_left["x"], hip_right["x"]),
            __get_central_point(hip_left["y"], hip_right["y"]),
        )

        #   Cálculo do tamanho do torso
        raw_scale = dist(shoulder_center, hip_center)
        scale = get_smoothed_scale(person_id, raw_scale)

        if scale is None:
            continue

        # Normalização do corpo por partes em relação ao torso centralizado

        trunk_angle = get_trunk_angle(shoulder_center, hip_center)

        normalized_parts = {}

        for body_part_id, body_part in smoothed_points.items():
            normalized_parts[body_part_id] = __normalize_body_part(
                scale, hip_center, body_part
            )

        # Análise PCA da nuvem de keypoints normalizados do frame:
        # descreve o alongamento (aspect ratio) e a orientação da silhueta
        pca_ratio, raw_pca_angle = get_pca_features(normalized_parts)
        pca_angle = align_and_store_pca_angle(person_id, raw_pca_angle)

        normalized_data[person_id] = {
            "coordinates": normalized_parts,
            "trunk_angle": trunk_angle,
            "pca_ratio": pca_ratio,
            "pca_angle": pca_angle,
        }

    return normalized_data


def process_frame(frame: np.ndarray, capture_date: float) -> dict[int, dict[str, Any]]:
    """
    Processa o frame capturado para obtenção das coordenadas dos keypoints dos corpos detectados no frame,
    aplica o filtro de Kalman para suavização das posições e normalização das coordenadas para o tamanho da imagem.
    Retorna um dicionário com os IDs dos corpos detectados e suas coordenadas normalizadas.
    """
    try:
        model = get_yolo_model()

        track_result = model.track(
            frame,
            device="cpu",
            conf=0.25,
            verbose=False,
            persist=True,
            tracker="botsort.yaml",
            classes=[0],
        )  # 0 = pessoa

        if len(track_result) <= 0:
            return

        frame_results = {}
        active_ids = []

        for result in track_result:
            kpts = result.keypoints

            if kpts is None or kpts.data is None or len(kpts.data) <= 0:
                continue

            boxes = result.boxes
            ids_tensor = getattr(boxes, "id", None)

            person_ids = (
                [int(ids_tensor[i].item()) for i in range(len(kpts.data))]
                if ids_tensor is not None and len(ids_tensor) >= len(kpts.data)
                else list(range(len(kpts.data)))
            )

            points = {}

            for person_id, person_kpts in zip(person_ids, kpts.data):
                kpts_np = person_kpts.numpy()

                points = {
                    idx: valor.tolist()
                    for idx, valor in enumerate(kpts_np)
                    if valor[2] != 0.0
                }

                # Aplicação do filtro de Kalman para suavização das posições
                smoothed_points = apply_kalman(person_id, capture_date, points)
                active_ids.append(person_id)
                frame_results[person_id] = (points, smoothed_points)

        # Remoção de trackers inativos
        cleanup_stale_trackers(set(active_ids))

        result = {}

        # Dados normalizados = Dados adimensionais

        for person_id, body_parts in __normalize_data(frame_results).items():
            result[person_id] = {
                "coordinates": body_parts["coordinates"],
                "trunk_angle": body_parts["trunk_angle"],
                "pca_ratio": body_parts["pca_ratio"],
                "pca_angle": body_parts["pca_angle"],
                "timestamp": capture_date,
            }

        return result

    except Exception as error:
        raise RuntimeError(f"Erro ao processar o frame: {error}") from error
