"""Um keypoint: rótulo, coordenadas e confiança."""


class BodyData:  # pylint: disable=too-few-public-methods
    """Um keypoint: rótulo, coordenadas normalizadas e confiança."""

    def __init__(self, label: str, x: float, y: float, conf: float) -> None:
        self.label = label
        self.x = x
        self.y = y
        self.conf = conf
