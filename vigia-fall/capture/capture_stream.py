"""
Módulo para o processo de streaming de vídeo
"""

import numpy as np


from shared import get_device_identity, get_network_settings


def stream_video(frame: np.ndarray) -> None:
    """
    Realizar o processo de streaming de vídeo capturado pelo dispositivo
    """
    service_url = get_network_settings().api_base_url
    device_id = get_device_identity().device_id

    url = f"{service_url}/live/{device_id}"
