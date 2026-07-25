"""
Variáveis de ambiente do projeto
"""

from dataclasses import dataclass
from functools import lru_cache
import os
from .helpers import helpers_convert_to_bool
from dotenv import load_dotenv


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
            data_dir=os.getenv("DATA_DIR"),
        )


@lru_cache
def get_settings() -> Settings:
    """
    Carregas as configurações de ambiente
    """
    return Settings.from_env()
