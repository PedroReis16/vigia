""" "
Helpers para extração de features
"""


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
    current_position: float,
    current_timestamp: float,
    previous_position: float,
    previous_timestamp: float,
) -> float:
    """
    Calcula a velocidade angular de um corpo a partir de suas coordenadas e do tempo.
    """
    # w(t) = (p(t) - p(t-1)) / (t - t-1)

    return (current_position - previous_position) / (
        current_timestamp - previous_timestamp
    )
