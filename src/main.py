"""Ponto de entrada da aplicação.

Modos de execução:
  --webcam          Visualização usando a câmera (webcam).
  --video PATH      Visualização usando arquivo de vídeo (mesma lógica de captura da webcam).
  (nenhum)          Modo padrão: usa configuração do .env (WEBCAM_PREVIEW_ENABLED, etc.).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.bootstrap import run, run_preview


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="older-fall: preview de câmera/vídeo com captura de sequências para LSTM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--webcam",
        action="store_true",
        help="Abre a visualização usando a webcam.",
    )
    group.add_argument(
        "--video",
        type=str,
        metavar="VIDEO_PATH",
        help="Abre a visualização usando o arquivo de vídeo indicado (mesma lógica de captura da webcam).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.webcam:
        run_preview(video_source=None)
        return
    if args.video:
        path = Path(args.video)
        if not path.exists():
            print(f"Erro: arquivo de vídeo não encontrado: {path}", file=sys.stderr)
            sys.exit(1)
        run_preview(video_source=path)
        return

    run()


if __name__ == "__main__":
    main()
