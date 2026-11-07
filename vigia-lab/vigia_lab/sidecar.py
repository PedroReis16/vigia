"""Arquivos ao lado do vídeo gravado pelo gravador leve.

  <take>_frames.npz   t_mono, t_wall, brightness por frame GRAVADO (mesma ordem do vídeo)
  <take>_capture.json cenário, política de duração, marcas, métricas e veredito da captura

O tempo real de cada frame é o que a análise offline usa; o fps do contêiner é só nominal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class FrameClock:
    t_mono: np.ndarray
    t_wall: np.ndarray
    brightness: np.ndarray

    def __len__(self) -> int:
        return len(self.t_mono)

    @property
    def t_rel(self) -> np.ndarray:
        return self.t_mono - self.t_mono[0] if len(self.t_mono) else self.t_mono


def sidecar_paths(video_path: Path) -> dict[str, Path]:
    stem = video_path.with_suffix("")
    return {"frames": Path(f"{stem}_frames.npz"), "capture": Path(f"{stem}_capture.json")}


def save_frames(path: Path, clock: FrameClock) -> None:
    np.savez_compressed(path, t_mono=clock.t_mono, t_wall=clock.t_wall, brightness=clock.brightness)


def load_frames(path: Path) -> FrameClock:
    z = np.load(path)
    return FrameClock(z["t_mono"], z["t_wall"], z["brightness"])


def save_capture_meta(path: Path, meta: dict[str, Any]) -> None:
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=_default), encoding="utf-8")


def load_capture_meta(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _default(o: Any) -> Any:
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"não serializável: {type(o)}")
