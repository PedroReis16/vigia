"""device.json: migração dos JSON legados e actualização por secção."""

from __future__ import annotations

import json
import os

import pytest

from shared import device_config as dc
from shared import settings as st


@pytest.fixture
def data_dir(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    st.get_settings.cache_clear()
    yield tmp_path
    st.get_settings.cache_clear()


def _read(data_dir) -> dict:
    return json.loads((data_dir / "device.json").read_text(encoding="utf-8"))


def test_migra_legados_e_apaga_os_ficheiros(data_dir) -> None:
    (data_dir / "identity.json").write_text(
        json.dumps(
            {
                "device_id": "dev-1",
                "device_name": "Vigia-test",
                "mac_address": "aa",
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "network.json").write_text(
        json.dumps({"ssid": "casa", "password": "x"}),
        encoding="utf-8",
    )
    (data_dir / "classifier.json").write_text(
        json.dumps({"classifier": "gru"}),
        encoding="utf-8",
    )
    (data_dir / "options.json").write_text(
        json.dumps({"clips": True, "blur": False}),
        encoding="utf-8",
    )

    assert dc.is_provisioned() is True
    data = _read(data_dir)
    assert data["identity"]["device_id"] == "dev-1"
    assert data["network"]["ssid"] == "casa"
    assert data["classifier"] == "gru"
    assert data["options"] == {"clips": True, "blur": False}
    for name in ("identity.json", "network.json", "classifier.json", "options.json"):
        assert not (data_dir / name).exists()
    if os.name == "posix":
        assert (data_dir / "device.json").stat().st_mode & 0o777 == 0o600


def test_migra_clips_e_blur_quando_options_nao_existe(data_dir) -> None:
    (data_dir / "clips.json").write_text(
        json.dumps({"enabled": True}), encoding="utf-8"
    )
    (data_dir / "blur.json").write_text(
        json.dumps({"enabled": False}), encoding="utf-8"
    )

    assert dc.read_section("options") == {"clips": True, "blur": False}
    assert not (data_dir / "clips.json").exists()
    assert not (data_dir / "blur.json").exists()


def test_device_existente_ignora_legados(data_dir) -> None:
    (data_dir / "device.json").write_text(
        json.dumps({"identity": {"device_id": "novo"}}),
        encoding="utf-8",
    )
    (data_dir / "identity.json").write_text(
        json.dumps({"device_id": "velho"}),
        encoding="utf-8",
    )

    assert dc.read_section("identity") == {"device_id": "novo"}
    assert (data_dir / "identity.json").exists()


def test_remove_network_preserva_identity(data_dir) -> None:
    dc.replace_section("identity", {"device_id": "x"})
    dc.replace_section(
        "network",
        {"ssid": "casa", "password": "old"},
    )
    dc.remove_section("network")

    data = _read(data_dir)
    assert data["identity"] == {"device_id": "x"}
    assert "network" not in data
    assert dc.is_provisioned() is False


def test_sem_legados_nao_cria_ficheiro(data_dir) -> None:
    assert dc.read_document() == {}
    assert not (data_dir / "device.json").exists()
    dc.remove_section("network")
    assert not (data_dir / "device.json").exists()
