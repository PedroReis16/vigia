"""
Variáveis de ambiente do projeto
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
from .helpers import helpers_convert_to_bool
from . import test_device_seed

logger = logging.getLogger(__name__)


def _parse_capture_source(raw: str) -> int | str:
    """
    Índice de câmera (ex.: "0") ou caminho/URL de vídeo (ex.: "~/Downloads/queda.mp4").
    """
    value = raw.strip()
    if value.lstrip("-").isdigit():
        return int(value)
    return str(Path(value).expanduser().resolve())


def _parse_state_log_mode(raw: str) -> str:
    mode = (raw or "verbose").strip().lower()
    if mode not in ("verbose", "changes", "heartbeat"):
        return "verbose"
    return mode


@dataclass(frozen=True)
class Settings:  # pylint: disable=too-many-instance-attributes
    """
    Configurações do programa
    """

    capture_source: int | str = 0
    capture_loop: bool = False
    show_video: bool = False
    yolo_pose_model: str = "yolo26s-pose"
    frame_rate: int = 12
    slider_window_size: int = 30
    data_dir: str = "/opt/vigia"
    debug: bool = True
    wifi_mock_result: str = "success"
    state_log_mode: str = "verbose"
    state_log_interval_s: float = 2.0

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Carrega as configurações do ambiente
        """
        load_dotenv()

        return cls(
            capture_source=_parse_capture_source(os.getenv("CAPTURE_SOURCE", "0")),
            capture_loop=helpers_convert_to_bool(os.getenv("CAPTURE_LOOP", "false")),
            show_video=helpers_convert_to_bool(os.getenv("SHOW_VIDEO", "false")),
            yolo_pose_model=os.getenv("YOLO_POSE_MODEL", "yolo26s-pose"),
            frame_rate=int(os.getenv("FRAME_RATE", "12")),
            slider_window_size=int(os.getenv("SLIDER_WINDOW", "30")),
            data_dir=os.getenv("DATA_DIR", "/opt/vigia") or "/opt/vigia",
            debug=helpers_convert_to_bool(os.getenv("DEBUG", "true")),
            wifi_mock_result=os.getenv("WIFI_MOCK_RESULT", "success").strip().lower(),
            state_log_mode=_parse_state_log_mode(os.getenv("STATE_LOG_MODE", "verbose")),
            state_log_interval_s=float(os.getenv("STATE_LOG_INTERVAL_S", "2.0")),
        )


@lru_cache(maxsize=1)
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


def get_classifier_path() -> Path:
    """Preferência de classificador (math|gru) escrita pelo bootstrap."""
    return Path(os.path.join(get_settings().data_dir, "classifier.json"))


@dataclass(frozen=True)
class DeviceIdentity:
    """
    Identidade do dispositivo
    """

    device_id: str
    device_name: str
    sign_priv: str
    ecdh_priv: str

    @classmethod
    def from_json(cls) -> "DeviceIdentity":
        """
        Cria uma instância de DeviceIdentity a partir de um arquivo JSON
        """
        identity_path = get_identity_path()

        if not identity_path.exists():
            raise Exception("Identity file not found")

        identity = json.loads(identity_path.read_text())

        return cls(
            device_id=identity["device_id"],
            device_name=identity["device_name"],
            sign_priv=identity["sign_priv"],
            ecdh_priv=identity["ecdh_priv"],
        )

    def with_sign_priv(self, sign_priv: str) -> "DeviceIdentity":
        return DeviceIdentity(
            device_id=self.device_id,
            device_name=self.device_name,
            sign_priv=sign_priv,
            ecdh_priv=self.ecdh_priv,
        )


def _align_test_device_sign_key(identity: DeviceIdentity) -> DeviceIdentity:
    """
    Em DEBUG, se identity aponta ao device seedado da API, garante o
    SignPrivateKey do TestDeviceSeed (a API sobrescreve SignPublicKey).
    """
    if not get_settings().debug:
        return identity

    if identity.device_id.lower() != test_device_seed.DEVICE_ID:
        return identity

    if identity.sign_priv.lower() == test_device_seed.SIGN_PRIVATE_KEY:
        return identity

    aligned = identity.with_sign_priv(test_device_seed.SIGN_PRIVATE_KEY)
    identity_path = get_identity_path()
    identity_path.write_text(
        json.dumps(
            {
                "device_id": aligned.device_id,
                "device_name": aligned.device_name,
                "sign_priv": aligned.sign_priv,
                "ecdh_priv": aligned.ecdh_priv,
            }
        )
    )
    identity_path.chmod(0o600)
    logger.info(
        "Device identity: SignPrivateKey alinhada ao TestDeviceSeed (DEBUG) "
        "para device_id=%s",
        aligned.device_id,
    )
    return aligned


@lru_cache(maxsize=1)
def get_device_identity() -> DeviceIdentity:
    """
    Retorna a identidade do dispositivo
    """
    return _align_test_device_sign_key(DeviceIdentity.from_json())


# Network Settings
@dataclass(frozen=True)
class NetworkSettings:
    """
    Configurações de rede do dispositivo
    """
    ssid: str
    password: str
    api_base_url: str
    fiware_api_key: str

    @classmethod
    def from_json(cls) -> "NetworkSettings":
        """
        Cria uma instância de NetworkSettings a partir de um arquivo JSON
        """
        network_path = get_network_path()
        
        if not network_path.exists():
            raise Exception("Network file not found")

        network = json.loads(network_path.read_text())

        return cls(
            ssid=network["ssid"],
            password=network["password"],
            api_base_url=network["api_base_url"],
            fiware_api_key=network["fiware_api_key"],
        )
        
@lru_cache(maxsize=1)
def get_network_settings() -> NetworkSettings:
    """
    Retorna as configurações de rede do dispositivo
    """
    return NetworkSettings.from_json()