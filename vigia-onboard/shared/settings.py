from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv  # type: ignore

from .paths import onboard_root

# Defaults da placa (systemd). Em debug local use DATA_DIR fora de /opt/vigia.
PROD_DATA_DIR = "/opt/vigia"
PROD_OTA_DIR = "/var/lib/vigia/ota"


def _parse_capture_source(raw: str) -> int | str:
    """Índice de câmera (ex.: "0") ou caminho/URL de vídeo."""
    value = raw.strip()
    if value.lstrip("-").isdigit():
        return int(value)
    return str(Path(value).expanduser().resolve())


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in ("1", "true", "t", "yes", "y")


def _wifi_mock_from_env(debug: bool) -> bool:
    """Sem WIFI_MOCK explícito, o mock segue o DEBUG (dev local ligado, placa desligada)."""
    raw = os.getenv("WIFI_MOCK")
    if raw is None or raw.strip() == "":
        return debug
    return _parse_bool(raw)


def _load_onboard_env() -> None:
    load_dotenv(onboard_root() / ".env")


@dataclass(frozen=True)
class Settings:
    """Configurações de captura e provisionamento."""

    capture_source: int | str = 0
    show_video: bool = False
    capture_loop: bool = False
    yolo_model: str = "yolo26s-pose"
    show_plot: bool = False
    blur_video: bool = False
    frame_rate: int = 12
    classifier: str = "math"
    slider_window_size: int = 30
    fall_shm_name: str = "vigia-onboard-fall"
    stream_control_shm_name: str = "vigia-onboard-stream-ctrl"
    live_shm_name: str = "vigia-onboard-live"
    clip_shm_name: str = "vigia-onboard-clip"
    clip_window_s: int = 30
    # JPEG 1080p em qualidade máxima cabe aqui. O slot não reserva o frame cru
    # (1920×1080×3), para a janela não competir com o YOLO por RAM.
    clip_max_payload: int = 2 * 1024 * 1024
    data_dir: str = PROD_DATA_DIR
    debug: bool = True
    ble_enabled: bool = True
    wifi_mock: bool = True
    wifi_mock_result: str = "success"
    mock_wifi_ssid: str = "local-mock"
    mock_wifi_password: str = "unused"
    mock_api_base_url: str = "http://localhost:8090/vigia"
    mock_fiware_api_key: str = "VIGIA"
    mock_stream_ingest_url: str = "rtmp://localhost:1935"

    def clip_slots_for(self, fps: int) -> int:
        """Slots da janela ≈ CLIP_WINDOW_S × fps de captura da câmera."""
        return max(1, int(self.clip_window_s) * max(1, int(fps)))

    @property
    def clip_slot_count(self) -> int:
        """Fallback com FRAME_RATE quando o fps da câmera ainda não foi lido."""
        return self.clip_slots_for(self.frame_rate)

    @classmethod
    def from_env(cls) -> Settings:
        """Carrega as configurações do `.env` da raiz do onboard."""
        _load_onboard_env()
        classifier = os.getenv("CLASSIFIER", "math").strip().lower()
        if classifier not in ("math", "gru"):
            classifier = "math"
        debug = _parse_bool(os.getenv("DEBUG", "true"))
        return cls(
            capture_source=_parse_capture_source(os.getenv("CAPTURE_SOURCE", "0")),
            show_video=_parse_bool(os.getenv("SHOW_VIDEO", "false")),
            capture_loop=_parse_bool(os.getenv("CAPTURE_LOOP", "false")),
            yolo_model=os.getenv("YOLO_MODEL", "yolo26s-pose"),
            show_plot=_parse_bool(
                os.getenv("SHOW_PLOT", "false")
            ),  # TODO: Adicionar essa propriedade como um valor dinâmico
            blur_video=_parse_bool(
                os.getenv("BLUR_VIDEO", "false")
            ),  # TODO: Adicionar essa propriedade como um valor dinâmico
            frame_rate=int(os.getenv("FRAME_RATE", "12")),
            classifier=classifier,
            slider_window_size=int(os.getenv("SLIDER_WINDOW", "30")),
            fall_shm_name=os.getenv("FALL_SHM_NAME", "vigia-onboard-fall").strip()
            or "vigia-onboard-fall",
            stream_control_shm_name=os.getenv(
                "STREAM_CONTROL_SHM_NAME", "vigia-onboard-stream-ctrl"
            ).strip()
            or "vigia-onboard-stream-ctrl",
            live_shm_name=os.getenv("LIVE_SHM_NAME", "vigia-onboard-live").strip()
            or "vigia-onboard-live",
            clip_shm_name=os.getenv("CLIP_SHM_NAME", "vigia-onboard-clip").strip()
            or "vigia-onboard-clip",
            clip_window_s=max(1, int(os.getenv("CLIP_WINDOW_S", "30"))),
            clip_max_payload=max(
                1, int(os.getenv("CLIP_MAX_PAYLOAD", str(2 * 1024 * 1024)))
            ),
            data_dir=os.getenv("DATA_DIR", PROD_DATA_DIR) or PROD_DATA_DIR,
            debug=debug,
            ble_enabled=_parse_bool(os.getenv("BLE_ENABLED", "true")),
            wifi_mock=_wifi_mock_from_env(debug),
            wifi_mock_result=os.getenv("WIFI_MOCK_RESULT", "success").strip().lower()
            or "success",
            mock_wifi_ssid=os.getenv("MOCK_WIFI_SSID", "local-mock").strip()
            or "local-mock",
            mock_wifi_password=os.getenv("MOCK_WIFI_PASSWORD", "unused"),
            mock_api_base_url=(
                os.getenv("MOCK_API_BASE_URL")
                or os.getenv("VIGIA_API_BASE_URL")
                or "http://localhost:8090/vigia"
            ).rstrip("/"),
            mock_fiware_api_key=(
                os.getenv("MOCK_FIWARE_API_KEY")
                or os.getenv("VIGIA_FIWARE_API_KEY")
                or "VIGIA"
            ).strip()
            or "VIGIA",
            mock_stream_ingest_url=(
                os.getenv("MOCK_STREAM_INGEST_URL")
                or os.getenv("VIGIA_STREAM_INGEST_URL")
                or "rtmp://localhost:1935"
            ).rstrip("/"),
        )


@lru_cache
def get_settings() -> Settings:
    """Carrega as configurações de ambiente (singleton)."""
    return Settings.from_env()


def get_identity_path() -> Path:
    """Caminho de identity.json (bootstrap / seed local)."""
    return Path(get_settings().data_dir) / "identity.json"


def get_network_path() -> Path:
    """Caminho de network.json (interface / seed local)."""
    return Path(get_settings().data_dir) / "network.json"


def get_classifier_path() -> Path:
    """Caminho de classifier.json (preferência math|gru)."""
    return Path(get_settings().data_dir) / "classifier.json"


def get_clips_config_path() -> Path:
    """Caminho de clips.json (preferência de armazenamento de clipes)."""
    return Path(get_settings().data_dir) / "clips.json"


def resolve_ota_dir() -> Path:
    """
    Diretório OTA: VIGIA_OTA_DIR explícito, senão {DATA_DIR}/ota em dev local,
    ou /var/lib/vigia/ota na instalação da placa (DATA_DIR=/opt/vigia).
    """
    explicit = (os.getenv("VIGIA_OTA_DIR") or "").strip()
    if explicit:
        return Path(explicit)
    data_dir = (get_settings().data_dir or PROD_DATA_DIR).rstrip("/") or PROD_DATA_DIR
    if data_dir != PROD_DATA_DIR:
        return Path(data_dir) / "ota"
    return Path(PROD_OTA_DIR)


def resolve_install_root() -> Path:
    """Raiz de instalação do onboard: VIGIA_INSTALL_ROOT ou DATA_DIR."""
    explicit = (os.getenv("VIGIA_INSTALL_ROOT") or "").strip()
    if explicit:
        return Path(explicit)
    return Path(get_settings().data_dir or PROD_DATA_DIR)


@dataclass(frozen=True)
class DeviceIdentity:
    """Identidade do dispositivo (device_id e nome)."""

    device_id: str
    device_name: str

    @classmethod
    def from_json(cls) -> DeviceIdentity:
        identity_path = get_identity_path()
        if not identity_path.exists():
            raise FileNotFoundError(f"Identity file not found: {identity_path}")
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        return cls(
            device_id=identity["device_id"],
            device_name=identity["device_name"],
        )


@lru_cache(maxsize=1)
def get_device_identity() -> DeviceIdentity:
    """Retorna a identidade do dispositivo."""
    return DeviceIdentity.from_json()


@dataclass(frozen=True)
class NetworkSettings:
    """Credenciais de rede e endpoints cloud (FIWARE / API / stream)."""

    ssid: str
    password: str
    api_base_url: str
    fiware_api_key: str
    stream_ingest_url: str

    @classmethod
    def from_json(cls) -> NetworkSettings:
        network_path = get_network_path()
        if not network_path.exists():
            raise FileNotFoundError(f"Network file not found: {network_path}")
        network = json.loads(network_path.read_text(encoding="utf-8"))
        return cls(
            ssid=network["ssid"],
            password=network["password"],
            api_base_url=network["api_base_url"],
            fiware_api_key=network["fiware_api_key"],
            stream_ingest_url=str(network.get("stream_ingest_url") or "").strip(),
        )


@lru_cache(maxsize=1)
def get_network_settings() -> NetworkSettings:
    """Retorna as configurações de rede do dispositivo."""
    return NetworkSettings.from_json()
