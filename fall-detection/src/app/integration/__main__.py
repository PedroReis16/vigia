"""
Ponto de entrada: ``python -m app.integration``.

Use ``pip install -e .`` na raiz do projeto ou ``cd src`` para o ``-m`` encontrar o pacote.
"""

from app.config import Settings
from app.integration import run_integration

from app.path_setup import ensure_src_on_path

ensure_src_on_path()

def main() -> None:
    run_integration(Settings.from_env())

if __name__ == "__main__":
    main()