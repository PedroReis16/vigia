"""Converte vídeo AVI para MP4 via ffmpeg.

Requer ffmpeg no PATH (ou em caminhos comuns de Linux/macOS Homebrew).

Uso (a partir de seed-codes/ ou da raiz do repo):
  python video_converter.py caminho/video.avi
  python video_converter.py caminho/video.avi -o saida.mp4
  python video_converter.py caminho/video.avi --copy
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _ffmpeg_executable() -> str:
    """Resolve o ffmpeg do sistema (Linux, macOS Homebrew, Windows PATH)."""
    unix_candidates = (
        "/usr/bin/ffmpeg",
        "/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
    )
    if sys.platform != "win32":
        for candidate in unix_candidates:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate

    for name in ("ffmpeg.exe", "ffmpeg"):
        found = shutil.which(name)
        if found:
            return found
    return "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"


def convert_avi_to_mp4(
    input_path: Path,
    output_path: Path,
    *,
    copy_streams: bool = False,
) -> None:
    if not input_path.is_file():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")
    if input_path.suffix.lower() != ".avi":
        raise ValueError(f"Entrada deve ser .avi, recebido: {input_path.suffix}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = _ffmpeg_executable()

    cmd = [
        ffmpeg,
        "-hide_banner",
        "-y",
        "-i",
        str(input_path),
    ]
    if copy_streams:
        cmd.extend(["-c", "copy"])
    else:
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
            ]
        )
    cmd.append(str(output_path))

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg não encontrado. Instale e garanta que está no PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"ffmpeg falhou (exit {exc.returncode}) ao converter {input_path}"
        ) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Converte um vídeo AVI para MP4 (H.264/AAC por padrão)."
    )
    parser.add_argument("input", type=Path, help="Caminho do arquivo .avi")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Caminho do .mp4 de saída (padrão: mesmo nome com extensão .mp4)",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Remux sem reencodar (-c copy). Mais rápido; falha se codecs forem incompatíveis com MP4.",
    )
    args = parser.parse_args(argv)

    input_path = args.input.expanduser().resolve()
    output_path = (
        args.output.expanduser().resolve()
        if args.output is not None
        else input_path.with_suffix(".mp4")
    )

    try:
        convert_avi_to_mp4(input_path, output_path, copy_streams=args.copy)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"OK: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
