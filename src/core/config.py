from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="older-fall")
    environment: str = Field(default="dev")
    log_level: str = Field(default="INFO")
    app_runtime_mode: Literal["api", "local", "embedded"] = Field(default="local")
    # api_host: str = Field(default="127.0.0.1")
    # api_port: int = Field(default=8000)

    model_confidence_threshold: float = Field(default=0.65)

    webcam_preview_enabled: bool = Field(default=False)
    webcam_index: str = Field(default="0,1")
    webcam_window_name: str = Field(default="older-fall webcam")
    webcam_flip_horizontal: bool = Field(default=False)
    # Modo debug: usa arquivo de vídeo em vez da câmera (mesma lógica YOLO/sequências)
    webcam_debug_video: str | None = Field(default=None)

    # Janela LSTM: quantidade de frames por captura (tecla c / buffer deslizante)
    frame_interval: int = Field(default=10, ge=1)

    yolo_model_path: str = Field(default="yolov8s.pt")

    # replication_enabled: bool = Field(default=False)
    # replication_url: str | None = Field(default=None)
    # replication_urls: list[str] = Field(default_factory=list)
    # replication_auth_token: str | None = Field(default=None)
    # replication_timeout_seconds: float = Field(default=2.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def webcam_indices(self) -> list[int]:
        """Parse comma-separated camera indices from config."""
        try:
            return [int(idx.strip()) for idx in self.webcam_index.split(",") if idx.strip()]
        except (ValueError, AttributeError):
            return [0]

    # @field_validator("replication_urls", mode="before")
    # @classmethod
    # def parse_replication_urls(cls, value: object) -> object:
    #     if isinstance(value, str):
    #         return [item.strip() for item in value.split(",") if item.strip()]
    #     return value

    # @property
    # def replication_targets(self) -> list[str]:
    #     targets = [*self.replication_urls]
    #     if self.replication_url:
    #         targets.append(self.replication_url)
    #     return list(dict.fromkeys(targets))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
