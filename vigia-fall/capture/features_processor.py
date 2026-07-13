"""
Processamento das features de uma janela deslizante
"""

from capture.models.feature_helpers import (
    get_linear_speed,
    get_angular_speed,
)


def extract_features(
    person_id: int, window_coordinates: list
) -> dict[int, dict[str, list[float]]]:
    """
    Extrai as features (ex.: velocidade linear) de cada parte do corpo
    ao longo de uma janela deslizante.

    Retorna um dicionário no formato:
        { keypoint_id: {"linear_speed_x": [...], "linear_speed_y": [...]} }
    """

    features: dict[int, dict[str, list[float]]] = {}

    # posição e timestamp do frame anterior, mantidos por parte do corpo
    previous_positions: dict[int, tuple[float, float]] = {}
    previous_timestamps: dict[int, float] = {}

    for frame in window_coordinates:
        current_ts = frame["timestamp"]
        body_parts = frame["coordinates"]

        for part, (current_x, current_y) in body_parts.items():
            # primeira vez que vemos essa parte: não há frame anterior p/ comparar
            if part not in previous_positions:
                features.setdefault(
                    part,
                    {"linear_speed_x": [], "linear_speed_y": [], "angular_speed": []},
                )
                previous_positions[part] = (current_x, current_y)
                previous_timestamps[part] = current_ts
                continue

            previous_position = previous_positions[part]
            previous_x, previous_y = previous_position
            previous_ts = previous_timestamps[part]

            speed_x = get_linear_speed(current_x, current_ts, previous_x, previous_ts)
            speed_y = get_linear_speed(current_y, current_ts, previous_y, previous_ts)
            angular_speed = get_angular_speed(
                (current_x, current_y), current_ts, previous_position, previous_ts
            )

            features[part]["linear_speed_x"].append(speed_x)
            features[part]["linear_speed_y"].append(speed_y)
            features[part]["angular_speed"].append(angular_speed)

            previous_positions[part] = (current_x, current_y)
            previous_timestamps[part] = current_ts

    print(f"Features extraídas para person_id={person_id}:")
    for part, part_features in features.items():
        print(f"  keypoint {part}: {part_features}")

    return features
