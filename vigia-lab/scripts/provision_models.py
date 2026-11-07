"""Copia os ONNX dos GRUs para vigia-lab/models/ e confere/gera o models.lock.json.

    python scripts/provision_models.py --src <fall-classifier-bench> [--write-lock]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vigia_lab import models_gru as mg  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, required=True, help="pasta fall-classifier-bench")
    ap.add_argument("--write-lock", action="store_true", help="grava os hashes atuais no lock")
    args = ap.parse_args()

    for src_name, dest in (
        ("gru_2classes.onnx", mg.GRU34_ONNX),
        ("gru_2classes_v2.onnx", mg.GRU37_ONNX),
    ):
        src = args.src / "model" / src_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"copiado {src} -> {dest}")

    canonical = args.src / "pose_features.py"
    if canonical.is_file():
        same = mg.file_sha256(canonical) == mg.file_sha256(mg.POSE_FEATURES)
        print(f"pose_features.py {'IGUAL' if same else 'DIVERGE'} do canônico")
        if not same:
            return 1

    if args.write_lock:
        import json

        mg.LOCK_PATH.write_text(json.dumps(mg.current_hashes(), indent=2) + "\n", encoding="utf-8")
        print(f"lock gravado em {mg.LOCK_PATH}")
    else:
        print("hashes OK" if mg.verify_lock() else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
