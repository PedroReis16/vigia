"""Smoke tests do provisionamento (skip BLE quando já há JSON)."""

from __future__ import annotations

import asyncio
import json
import threading
from uuid import UUID

from provision import identity, settings
from provision.runner import provision_supervisor


def test_is_provisioned_false_sem_ficheiros(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    assert identity.is_provisioned() is False


def test_is_provisioned_true_com_identity_e_network(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    (tmp_path / "identity.json").write_text("{}")
    (tmp_path / "network.json").write_text("{}")
    assert identity.is_provisioned() is True


def test_load_or_create_identity_persiste_e_reutiliza(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    monkeypatch.setattr(identity, "_mac_address", lambda: "aa:bb:cc:dd:ee:ff")

    first = identity.load_or_create_identity()
    second = identity.load_or_create_identity()

    assert first.device_id == second.device_id
    assert isinstance(first.device_id, UUID)
    data = json.loads((tmp_path / "identity.json").read_text())
    assert data["mac_address"] == "aa:bb:cc:dd:ee:ff"
    assert data["device_name"] == first.device_name
    assert "sign_priv" in data
    assert "ecdh_priv" in data


def test_supervisor_skips_ble_quando_ja_provisionado(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    (tmp_path / "identity.json").write_text("{}")
    (tmp_path / "network.json").write_text(
        json.dumps(
            {
                "ssid": "test",
                "password": "x",
                "api_base_url": "http://localhost",
                "fiware_api_key": "k",
            }
        )
    )

    called = {"start": 0}

    def fake_start() -> None:
        called["start"] += 1

    monkeypatch.setattr("provision.runner.start_fall_detection", fake_start)

    async def run() -> None:
        task = asyncio.create_task(provision_supervisor(threading.Event()))
        await asyncio.sleep(0.2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run())
    assert called["start"] >= 1
