"""Preparação do diretório de dados (DATA_PATH, ``coordinates/``, ``frames/``).

Usado por captura e ML sem acoplar um pacote ao outro; ambos dependem só de `config`.
"""

from __future__ import annotations

import os
import shutil

from app.config.settings import Settings
from app.logging import get_logger

logger = get_logger("config")


def prepare_data_workspace(settings: Settings, *, reset: bool = True) -> None:
    """
    Garante ``settings.data_path``, ``…/coordinates`` (CSVs de pose) e ``settings.frames_dir``.

    Se ``reset`` for verdadeiro e ``data_path`` estiver definido, remove a árvore
    existente antes de recriar (comportamento atual do runner de captura).

    Quando captura e ML rodam em processos paralelos, o processo que **não** deve
    apagar a pasta deve chamar com ``reset=False`` para evitar corrida com o outro.
    """
    if not settings.data_path:
        return
    if reset:
        logger.debug("removing data path: {}", settings.data_path)
        if os.path.isdir(settings.data_path):
            shutil.rmtree(settings.data_path)
    os.makedirs(settings.data_path, exist_ok=True)
    os.makedirs(os.path.join(settings.data_path, "coordinates"), exist_ok=True)
    if settings.frames_dir:
        os.makedirs(settings.frames_dir, exist_ok=True)
