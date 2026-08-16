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


def test_get_wifi_service_nmcli_por_omissao(monkeypatch) -> None:
    monkeypatch.delenv("WIFI_MOCK", raising=False)
    settings.get_settings.cache_clear()
    from provision.wifi import NmcliWifiService, get_wifi_service

    assert isinstance(get_wifi_service(), NmcliWifiService)
    settings.get_settings.cache_clear()


def test_get_wifi_service_mock_quando_wifi_mock(monkeypatch) -> None:
    monkeypatch.setenv("WIFI_MOCK", "true")
    settings.get_settings.cache_clear()
    from provision.wifi import MockWifiService, get_wifi_service

    assert isinstance(get_wifi_service(), MockWifiService)
    settings.get_settings.cache_clear()


def test_wifi_fail_nao_persiste_network(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()

    class FailWifi:
        async def connect(self, ssid, password):
            raise RuntimeError("ssid invalido")

    async def run() -> None:
        from provision.wifi import connect_and_persist

        await connect_and_persist("bad", "x", "http://api", "k", service=FailWifi())

    try:
        asyncio.run(run())
        raise AssertionError("esperava RuntimeError")
    except RuntimeError:
        pass
    assert not (tmp_path / "network.json").exists()
    settings.get_settings.cache_clear()


def test_wifi_ok_persiste_network(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()

    class OkWifi:
        async def connect(self, ssid, password):
            return None

    from provision.wifi import connect_and_persist

    async def run() -> None:
        await connect_and_persist("casa", "segredo", "http://api", "k", service=OkWifi())

    asyncio.run(run())
    data = json.loads((tmp_path / "network.json").read_text())
    assert data["ssid"] == "casa"
    assert data["password"] == "segredo"
    settings.get_settings.cache_clear()


def test_switch_network_falha_nao_persiste(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    (tmp_path / "network.json").write_text(
        json.dumps(
            {
                "ssid": "casa",
                "password": "old",
                "api_base_url": "http://api",
                "fiware_api_key": "k",
            }
        )
    )
    restored = {"n": 0}

    class FailThenRestore:
        async def connect(self, ssid, password):
            if ssid == "nova":
                raise RuntimeError("invalida")
            restored["n"] += 1

    async def run() -> None:
        from provision.wifi import switch_network

        ok = await switch_network("nova", "x", service=FailThenRestore())
        assert ok is False

    asyncio.run(run())
    data = json.loads((tmp_path / "network.json").read_text())
    assert data["ssid"] == "casa"
    assert restored["n"] == 1
    settings.get_settings.cache_clear()


def test_switch_network_ok_persiste(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    (tmp_path / "network.json").write_text(
        json.dumps(
            {
                "ssid": "casa",
                "password": "old",
                "api_base_url": "http://api",
                "fiware_api_key": "k",
            }
        )
    )

    class OkWifi:
        async def connect(self, ssid, password):
            return None

    async def run() -> None:
        from provision.wifi import switch_network

        ok = await switch_network("nova", "segredo", service=OkWifi())
        assert ok is True

    asyncio.run(run())
    data = json.loads((tmp_path / "network.json").read_text())
    assert data["ssid"] == "nova"
    assert data["password"] == "segredo"
    assert data["api_base_url"] == "http://api"
    settings.get_settings.cache_clear()


def test_parse_active_ssid() -> None:
    from provision.wifi import _parse_active_ssid

    listing = "no:Outra\nyes:Casa\nno:Vizinho\n"
    assert _parse_active_ssid(listing) == "Casa"
    assert _parse_active_ssid("no:Casa\n") is None


def test_wireless_names_for_ssid() -> None:
    from provision.wifi import _wireless_names_for_ssid

    listing = (
        "Casa:802-11-wireless\n"
        "Casa 1:802-11-wireless\n"
        "Wired connection 1:802-3-ethernet\n"
        "Outra:802-11-wireless\n"
    )
    names = _wireless_names_for_ssid(listing, "Casa")
    assert names == ["Casa", "Casa 1"]
