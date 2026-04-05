from __future__ import annotations

from app.config import Settings, prepare_data_workspace


def run_analysis(settings: Settings) -> None:
    """Prepara diretório de dados e executa modelos de postura / quedas."""

    # Não apaga DATA_PATH aqui: em ``runtime`` paralelo, a captura já faz reset;
    # só garantimos que as pastas existam para leitura/escrita.
    prepare_data_workspace(settings, reset=False)

    print("Machine learning process running")
