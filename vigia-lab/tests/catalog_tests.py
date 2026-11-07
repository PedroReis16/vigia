from pathlib import Path

import pytest

from vigia_lab.catalog import ScenarioCatalogError, load_catalog


def test_default_catalog_has_16_scenarios_5_falls() -> None:
    scenarios = load_catalog()
    assert len(scenarios) == 16
    assert sum(s.is_fall for s in scenarios) == 5


def test_duplicate_id_is_rejected(tmp_path: Path) -> None:
    f = tmp_path / "s.yaml"
    f.write_text("scenarios:\n  - {id: a, label: ADL}\n  - {id: a, label: FALL}\n", encoding="utf-8")
    with pytest.raises(ScenarioCatalogError):
        load_catalog(f)


def test_invalid_label_is_rejected(tmp_path: Path) -> None:
    f = tmp_path / "s.yaml"
    f.write_text("scenarios:\n  - {id: a, label: XYZ}\n", encoding="utf-8")
    with pytest.raises(ScenarioCatalogError):
        load_catalog(f)
