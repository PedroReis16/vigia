"""
Variáveis de ambiente do projeto
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
from .helpers import helpers_convert_to_bool


@dataclass(frozen=True)
class Settings:  # pylint: disable=too-many-instance-attributes
    """
    Configurações do programa
    """

    capture_source: int = 0
    show_video: bool = False
    yolo_pose_model: str = "yolo26s-pose"
    frame_rate: int = 12
    slider_window_size: int = 30
    data_dir: str = "/opt/vigia"
    debug: bool = True
    wifi_mock_result: str = "success"

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Carrega as configurações do ambiente
        """
        load_dotenv()

        return cls(
            capture_source=int(os.getenv("CAPTURE_SOURCE", "0")),
            show_video=helpers_convert_to_bool(os.getenv("SHOW_VIDEO", "false")),
            yolo_pose_model=os.getenv("YOLO_POSE_MODEL", "yolo26s-pose"),
            frame_rate=int(os.getenv("FRAME_RATE", "12")),
            slider_window_size=int(os.getenv("SLIDER_WINDOW", "30")),
            data_dir=os.getenv("DATA_DIR", "/opt/vigia") or "/opt/vigia",
            debug=helpers_convert_to_bool(os.getenv("DEBUG", "true")),
            wifi_mock_result=os.getenv("WIFI_MOCK_RESULT", "success").strip().lower(),
        )

@lru_cache
def get_settings() -> Settings:
    """
    Carregas as configurações de ambiente
    """
    return Settings.from_env()

def get_identity_path() -> Path:
    """
    Retorna o caminho do arquivo de identidade do dispositivo
    """
    return Path(os.path.join(get_settings().data_dir, "identity.json"))

def get_network_path() -> Path:
    """
    Retorna o caminho do arquivo de credenciais de rede do dispositivo
    """
    return Path(os.path.join(get_settings().data_dir, "network.json"))