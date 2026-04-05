"""PYTHONPATH=src python -m app (a partir da pasta fall-detection)."""

from app.config import Settings
from app.runtime import run


def main() -> None:
    """Ponto de entrada: configuração via ambiente e execução do runtime."""
    run(Settings.from_env())


if __name__ == "__main__":
    main()
