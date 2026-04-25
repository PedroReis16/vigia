"""Preparação do diretório de dados (DATA_PATH, ``coordinates/``, ``frames/``).

Usado por captura e ML sem acoplar um pacote ao outro; ambos dependem só de `config`.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from app.config.settings import Settings
from app.logging import get_logger

logger = get_logger("config")
DEFAULT_DATA_PATH = "data"


def resolve_data_root(data_path: str | None) -> Path:
    raw_path = (data_path or "").strip()
    return Path(raw_path or DEFAULT_DATA_PATH)


def resolve_data_root_from_env() -> Path:
    return resolve_data_root(os.getenv("DATA_PATH"))


def device_settings_path_from_env() -> Path:
    return resolve_data_root_from_env() / "device" / "device.json"


def prepare_data_workspace(settings: Settings, *, reset: bool = True) -> None:
    """
    Garante ``settings.data_path``, ``…/coordinates`` (CSVs de pose) e ``settings.frames_dir``.

    Se ``reset`` for verdadeiro e ``data_path`` estiver definido, remove a árvore
    existente antes de recriar (comportamento atual do runner de captura).

    Quando captura e ML rodam em processos paralelos, o processo que **não** deve
    apagar a pasta deve chamar com ``reset=False`` para evitar corrida com o outro.
    """
    data_root = resolve_data_root(settings.data_path)
    coordinates_dir = data_root / "coordinates"
    frames_dir = Path(settings.frames_dir) if settings.frames_dir else data_root / "frames"

    if reset:
        # Limpa apenas artefatos de captura/análise para preservar configurações persistentes.
        logger.debug("removing capture data directories under {}", data_root)
        if coordinates_dir.is_dir():
            shutil.rmtree(coordinates_dir)
        if frames_dir.is_dir():
            shutil.rmtree(frames_dir)

    data_root.mkdir(parents=True, exist_ok=True)
    coordinates_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)
