#!/usr/bin/env python3
"""Garante yolo26s-pose.pt na raiz de vigia-fall (download via Ultralytics se ausente)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

MODEL_STEM = "yolo26s-pose"
MODEL_FILE = f"{MODEL_STEM}.pt"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _find_downloaded_weight(root: Path) -> Path | None:
    candidates = [
        root / MODEL_FILE,
        Path.cwd() / MODEL_FILE,
        Path.home() / ".cache" / "ultralytics" / MODEL_FILE,
    ]
    for path in candidates:
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def main() -> int:
    root = _project_root()
    target = root / MODEL_FILE

    if target.is_file() and target.stat().st_size > 0:
        print(f"OK: {target} já existe ({target.stat().st_size} bytes)")
        return 0

    print(f"Baixando {MODEL_STEM} via Ultralytics para {target}...")
    prev = Path.cwd()
    try:
        os.chdir(root)
        from ultralytics import YOLO  # pyright: ignore[reportMissingImports]

        YOLO(MODEL_STEM)
    finally:
        os.chdir(prev)

    found = _find_downloaded_weight(root)
    if found is None:
        print(
            f"ERRO: download concluído mas {MODEL_FILE} não foi encontrado.",
            file=sys.stderr,
        )
        return 1

    if found.resolve() != target.resolve():
        shutil.copy2(found, target)

    if not target.is_file() or target.stat().st_size == 0:
        print(f"ERRO: falha ao gravar {target}", file=sys.stderr)
        return 1

    print(f"OK: {target} ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
