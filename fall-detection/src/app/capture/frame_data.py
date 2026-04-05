"""Estruturas simples para keypoints de uma pessoa em um frame."""


class BodyData:  # pylint: disable=too-few-public-methods
    """Um keypoint: rótulo, coordenadas normalizadas e confiança."""

    def __init__(self, label: str, x: float, y: float, conf: float) -> None:
        self.label = label
        self.x = x
        self.y = y
        self.conf = conf


class PersonData:  # pylint: disable=too-few-public-methods
    """Uma pessoa rastreada e a lista de keypoints válidos neste frame."""

    def __init__(self, person_id: int, body_data: list[BodyData]) -> None:
        self.person_id = person_id
        self.body_data = body_data
