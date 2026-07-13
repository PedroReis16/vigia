"""
Processamento das features de uma janela deslizante
"""

from typing import Any

from capture.models.feature_helpers import (
    get_linear_speed,
    get_angular_speed,
    get_linear_acceleration,
    get_angular_acceleration,
)


def extract_features(person_id: int, window_coordinates: list) -> list[dict[str, Any]]:
    """
    Extrai as features (velocidade e aceleração linear/angular) de cada parte do
    corpo ao longo de uma janela deslizante, mantendo o alinhamento com os
    frames de entrada.

    """

    features: list[dict[str, Any]] = []

    # posição e timestamp do frame anterior, mantidos por parte do corpo
    previous_positions: dict[int, tuple[float, float]] = {}
    previous_timestamps: dict[int, float] = {}

    # velocidades do instante anterior, usadas para derivar a aceleração
    previous_speeds: dict[int, tuple[float, float]] = {}
    previous_angular_speeds: dict[int, float] = {}
    previous_speed_timestamps: dict[int, float] = {}

    for frame in window_coordinates:
        current_ts = frame["timestamp"]
        body_parts = frame["coordinates"]

        frame_features: dict[str, Any] = {
            "timestamp": current_ts,
            "trunk_angle": frame.get("trunk_angle"),
            "pca_ratio": frame.get("pca_ratio"),
            "pca_angle": frame.get("pca_angle"),
            "parts": {},
        }

        for part, (current_x, current_y) in body_parts.items():
            part_features: dict[str, Any] = {
                "coordinates": (current_x, current_y),
                "linear_speed_x": 0.0,
                "linear_speed_y": 0.0,
                "angular_speed": 0.0,
                "linear_acceleration_x": 0.0,
                "linear_acceleration_y": 0.0,
                "angular_acceleration": 0.0,
            }

            # há frame anterior dessa parte: dá para calcular as velocidades
            if part in previous_positions:
                previous_position = previous_positions[part]
                previous_x, previous_y = previous_position
                previous_ts = previous_timestamps[part]

                speed_x = get_linear_speed(
                    current_x, current_ts, previous_x, previous_ts
                )
                speed_y = get_linear_speed(
                    current_y, current_ts, previous_y, previous_ts
                )
                angular_speed = get_angular_speed(
                    (current_x, current_y), current_ts, previous_position, previous_ts
                )

                part_features["linear_speed_x"] = speed_x
                part_features["linear_speed_y"] = speed_y
                part_features["angular_speed"] = angular_speed

                # há velocidade anterior: dá para derivar a aceleração
                if part in previous_speeds:
                    previous_speed_x, previous_speed_y = previous_speeds[part]
                    previous_angular_speed = previous_angular_speeds[part]
                    previous_speed_ts = previous_speed_timestamps[part]

                    part_features["linear_acceleration_x"] = get_linear_acceleration(
                        speed_x, current_ts, previous_speed_x, previous_speed_ts
                    )
                    part_features["linear_acceleration_y"] = get_linear_acceleration(
                        speed_y, current_ts, previous_speed_y, previous_speed_ts
                    )
                    part_features["angular_acceleration"] = get_angular_acceleration(
                        angular_speed,
                        current_ts,
                        previous_angular_speed,
                        previous_speed_ts,
                    )

                previous_speeds[part] = (speed_x, speed_y)
                previous_angular_speeds[part] = angular_speed
                previous_speed_timestamps[part] = current_ts

            previous_positions[part] = (current_x, current_y)
            previous_timestamps[part] = current_ts

            frame_features["parts"][part] = part_features

        features.append(frame_features)


    print(f"Features extraídas para person_id={person_id}:")
    print("--------------------------------")
    print("features: ", features)
    print("--------------------------------")

    return features
