# import uvicorn

from __future__ import annotations

from pathlib import Path

from src.core import get_settings
from src.runtime import LocalRuntime


def run() -> None:
    """Executa o runtime padrão (comportamento definido pelo .env)."""
    settings = get_settings()
    runtime = LocalRuntime(settings)
    runtime.run()


def run_preview(video_source: Path | str | None = None) -> None:
    """Executa apenas o preview de vídeo, com fonte definida pelo parâmetro.

    Chamado por main quando se usa --webcam ou --video <path>.
    Usa a mesma lógica de captura (manual/contínuo, YOLO, sequências) em ambos os modos.

    Args:
        video_source: None para webcam; caminho do arquivo para modo vídeo (debug).
    """
    settings = get_settings()
    runtime = LocalRuntime(settings, video_source=video_source)
    runtime.run_preview()
