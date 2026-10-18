"""Catálogo de cenários (scenarios.yaml): carga e validação na leitura."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CATALOG_PATH = Path(__file__).with_name("scenarios.yaml")

_SLUG_RE = re.compile(r"^[a-z0-9_]+$")
_VALID_LABELS = {"ADL", "FALL"}


class ScenarioCatalogError(ValueError):
    """scenarios.yaml malformado."""


@dataclass(frozen=True)
class Scenario:
    id: str
    label: str  # "ADL" ou "FALL"
    description: str = ""

    @property
    def is_fall(self) -> bool:
        return self.label == "FALL"


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> list[Scenario]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("scenarios")
    if not entries:
        raise ScenarioCatalogError(f"Nenhum cenário encontrado em {path}")

    scenarios: list[Scenario] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        scenario = _parse_entry(entry, index)
        if scenario.id in seen:
            raise ScenarioCatalogError(f"id duplicado no catálogo: '{scenario.id}'")
        seen.add(scenario.id)
        scenarios.append(scenario)
    return scenarios


def _parse_entry(entry: object, index: int) -> Scenario:
    if not isinstance(entry, dict):
        raise ScenarioCatalogError(f"entrada #{index}: formato inválido")

    scenario_id = entry.get("id")
    if not isinstance(scenario_id, str) or not _SLUG_RE.match(scenario_id):
        raise ScenarioCatalogError(
            f"entrada #{index}: 'id' ausente ou fora de {_SLUG_RE.pattern}"
        )
    label = entry.get("label")
    if label not in _VALID_LABELS:
        raise ScenarioCatalogError(
            f"cenário '{scenario_id}': label '{label}' deve ser um de {sorted(_VALID_LABELS)}"
        )
    return Scenario(id=scenario_id, label=label, description=entry.get("description") or "")
