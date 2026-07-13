""" "
Helpers para extração de features
"""

import math


def get_linear_speed(
    current_position: float,
    current_timestamp: float,
    previous_position: float,
    previous_timestamp: float,
) -> float:
    """
    Calcula a velocidade linear de um corpo a partir de suas coordenadas e do tempo.
    """
    # v(t) = (p(t) - p(t-1)) / (t - t-1)

    return (current_position - previous_position) / (
        current_timestamp - previous_timestamp
    )


def get_angular_speed(
    current_position: tuple[float, float],
    current_timestamp: float,
    previous_position: tuple[float, float],
    previous_timestamp: float,
) -> float:
    """
    Calcula a velocidade angular (rad/s) do vetor posição de um ponto,
    a partir da variação do ângulo entre dois instantes.
    """
    # w(t) = (theta(t) - theta(t-1)) / (t - t-1)

    current_angle = math.atan2(current_position[1], current_position[0])
    previous_angle = math.atan2(previous_position[1], previous_position[0])

    # normaliza a variação para [-pi, pi] p/ evitar saltos de 2*pi
    delta_angle = (current_angle - previous_angle + math.pi) % (2 * math.pi) - math.pi

    return delta_angle / (current_timestamp - previous_timestamp)

def get_trunk_angle(
    shoulder_center: tuple[float, float],
    hip_center: tuple[float, float],
) -> float:
    """
    Calcula o ângulo do tronco de um corpo a partir das coordenadas do ombro e do quadril.
    Retorna o ângulo em radianos com o posicionamento do tronco em relação ao eixo vertical
    """

    shoulder_x, shoulder_y = shoulder_center
    hip_x, hip_y = hip_center

    trunk_angle = math.atan2((hip_x - shoulder_x), (hip_y - shoulder_y))

    return trunk_angle
    