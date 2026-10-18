"""Numeração de takes e identificadores de sessão — lógica pura.

O próximo take é sempre maior que o maior número visto no manifest OU nos
nomes de arquivo em disco, para nunca sobrescrever uma gravação existente
(o manifest pode ter se perdido ou a gravação ter sido interrompida).
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_TAKE_RE = re.compile(r"_take(\d+)_p\d+\.npy$")


def next_take_number(existing: set[int]) -> int:
    return max(existing, default=0) + 1


def takes_from_filenames(scenario_dir: Path, scenario_id: str) -> set[int]:
    """Takes presentes em disco (só `.npy` de keypoints, não `_labels`/`_t`)."""
    if not scenario_dir.exists():
        return set()
    takes: set[int] = set()
    for path in scenario_dir.glob(f"{scenario_id}_take*.npy"):
        match = _TAKE_RE.search(path.name)
        if match:
            takes.add(int(match.group(1)))
    return takes


def take_id(scenario_id: str, take: int) -> str:
    return f"{scenario_id}_take{take:02d}"


def clip_id(scenario_id: str, take: int, person_idx: int) -> str:
    return f"{take_id(scenario_id, take)}_p{person_idx}"


def new_session_id(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
