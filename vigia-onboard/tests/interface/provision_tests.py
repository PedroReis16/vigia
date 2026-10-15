"""Smoke tests do provisionamento (skip BLE quando já há JSON)."""

from __future__ import annotations

import asyncio
import json
import threading
from uuid import UUID

from interface.provision import identity, settings
from interface.provision.runner import provision_supervisor


def _write_device(tmp_path, document: dict):
    path = tmp_path / "device.json"
    path.write_text(json.dumps(document))
    return path


def _read_device(tmp_path) -> dict:
    return json.loads((tmp_path / "device.json").read_text())


def test_load_or_create_identity_descarta_chaves_legadas(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    _write_device(
        tmp_path,
        {
            "identity": {
                "device_id": "11111111-1111-1111-1111-111111111111",
                "device_name": "Vigia-test",
                "mac_address": "aa:bb:cc:dd:ee:ff",
                "sign_priv": "11" * 32,
                "ecdh_priv": "22" * 32,
            }
        },
    )

    loaded = identity.load_or_create_identity()
    data = _read_device(tmp_path)["identity"]

    assert loaded.device_name == "Vigia-test"
    assert "sign_priv" not in data
    assert "ecdh_priv" not in data
    assert set(data) == {"device_id", "device_name", "mac_address"}


def test_is_provisioned_false_sem_ficheiros(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    assert identity.is_provisioned() is False


def test_is_provisioned_true_com_identity_e_network(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    _write_device(tmp_path, {"identity": {}, "network": {}})
    assert identity.is_provisioned() is True


def test_load_or_create_identity_persiste_e_reutiliza(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    monkeypatch.setattr(identity, "_mac_address", lambda: "aa:bb:cc:dd:ee:ff")

    first = identity.load_or_create_identity()
    second = identity.load_or_create_identity()

    assert first.device_id == second.device_id
    assert isinstance(first.device_id, UUID)
    data = _read_device(tmp_path)["identity"]
    assert data["mac_address"] == "aa:bb:cc:dd:ee:ff"
    assert data["device_name"] == first.device_name
    assert "sign_priv" not in data
    assert "ecdh_priv" not in data


def test_supervisor_skips_ble_quando_ja_provisionado(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    from interface.provision import state as pairing_state

    pairing_state.clear_force_pairing()
    _write_device(
        tmp_path,
        {
            "identity": {},
            "network": {
                "ssid": "test",
                "password": "x",
                "api_base_url": "http://localhost",
                "fiware_api_key": "k",
            },
        },
    )

    called = {"start": 0}

    def fake_start() -> None:
        called["start"] += 1

    monkeypatch.setattr("interface.provision.runner.start_capture", fake_start)

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
    data = _read_device(tmp_path)
    assert data["classifier"] == "math"
    assert "network" in data


def test_unlink_preserva_identity_e_network(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    from interface.provision import actions, state as pairing_state

    pairing_state.clear_force_pairing()
    payload = {"identity": {"device_id": "x"}, "network": {"ssid": "casa"}}
    _write_device(tmp_path, payload)
    fall_data = tmp_path / "fall-detection" / "data"
    fall_data.mkdir(parents=True)
    (fall_data / "cache.bin").write_text("x")
    (tmp_path / "DB").mkdir()
    (tmp_path / "DB" / "local.db").write_text("db")

    monkeypatch.setenv("VIGIA_RESET_SCRIPT", str(tmp_path / "missing-script"))
    monkeypatch.setattr(actions, "stop_capture", lambda: None)
    cancel = threading.Event()
    pairing_state.bind_cancel(cancel)

    actions.unlink_user()

    assert _read_device(tmp_path) == payload
    assert not fall_data.exists()
    assert not (tmp_path / "DB").exists()
    assert pairing_state.is_force_pairing() is True
    assert cancel.is_set()
    pairing_state.clear_force_pairing()
    pairing_state.bind_cancel(threading.Event())


def test_supervisor_abre_ble_apos_force_pairing(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLE_ENABLED", "true")
    settings.get_settings.cache_clear()
    from interface.provision import state as pairing_state

    pairing_state.clear_force_pairing()
    _write_device(
        tmp_path,
        {
            "identity": {
                "device_id": "11111111-1111-1111-1111-111111111111",
                "device_name": "Vigia-test",
                "mac_address": "aa:bb:cc:dd:ee:ff",
            },
            "network": {"ssid": "casa"},
        },
    )

    called = {"ble": 0, "start": 0}

    async def fake_beacon(*_args, **_kwargs) -> None:
        called["ble"] += 1
        pairing_state.clear_force_pairing()

    monkeypatch.setattr("interface.provision.runner.is_ble_available", lambda: True)
    monkeypatch.setattr("interface.provision.runner.init_register_beacon", fake_beacon)
    monkeypatch.setattr(
        "interface.provision.runner.start_capture",
        lambda: called.__setitem__("start", called["start"] + 1),
    )

    cancel = threading.Event()
    pairing_state.bind_cancel(cancel)

    async def run() -> None:
        task = asyncio.create_task(provision_supervisor(cancel))
        await asyncio.sleep(0.15)
        assert called["start"] >= 1
        assert called["ble"] == 0
        pairing_state.request_force_pairing()
        # O wait do supervisor faz sleep(1); dar margem para sair e abrir BLE.
        await asyncio.sleep(1.4)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run())
    assert called["ble"] >= 1
    pairing_state.clear_force_pairing()
    pairing_state.bind_cancel(threading.Event())
    settings.get_settings.cache_clear()


def test_supervisor_idle_sem_ble_quando_desactivado(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLE_ENABLED", "false")
    settings.get_settings.cache_clear()
    from interface.provision import state as pairing_state

    pairing_state.clear_force_pairing()
    identity.load_or_create_identity()

    called = {"ble": 0}

    async def fake_beacon(*_args, **_kwargs) -> None:
        called["ble"] += 1

    monkeypatch.setattr("interface.provision.runner.init_register_beacon", fake_beacon)

    async def run() -> None:
        task = asyncio.create_task(provision_supervisor(threading.Event()))
        await asyncio.sleep(0.3)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run())
    assert called["ble"] == 0
    settings.get_settings.cache_clear()


def test_is_ble_available_respeita_ble_enabled(monkeypatch) -> None:
    monkeypatch.setenv("BLE_ENABLED", "false")
    settings.get_settings.cache_clear()
    from interface.provision.ble import is_ble_available

    assert is_ble_available() is False
    settings.get_settings.cache_clear()


def test_ensure_mock_network_cria_network_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("WIFI_MOCK", "true")
    monkeypatch.setenv("MOCK_API_BASE_URL", "http://api.test/vigia")
    monkeypatch.setenv("MOCK_STREAM_INGEST_URL", "rtmp://ingest.test:1935")
    settings.get_settings.cache_clear()
    _write_device(tmp_path, {"identity": {"device_id": "x"}})

    async def run() -> None:
        from interface.provision.wifi import ensure_mock_network

        assert await ensure_mock_network() is True

    asyncio.run(run())
    data = _read_device(tmp_path)
    assert data["identity"] == {"device_id": "x"}
    assert data["network"]["ssid"] == "local-mock"
    assert data["network"]["api_base_url"] == "http://api.test/vigia"
    assert data["network"]["stream_ingest_url"] == "rtmp://ingest.test:1935"
    settings.get_settings.cache_clear()


def test_supervisor_provisiona_via_mock_sem_ble(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BLE_ENABLED", "false")
    monkeypatch.setenv("WIFI_MOCK", "true")
    settings.get_settings.cache_clear()
    from interface.provision import state as pairing_state

    pairing_state.clear_force_pairing()
    monkeypatch.setattr(identity, "_mac_address", lambda: "aa:bb:cc:dd:ee:ff")

    called = {"start": 0}
    monkeypatch.setattr(
        "interface.provision.runner.start_capture",
        lambda: called.__setitem__("start", called["start"] + 1),
    )

    async def run() -> None:
        task = asyncio.create_task(provision_supervisor(threading.Event()))
        await asyncio.sleep(1.5)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(run())
    assert "network" in _read_device(tmp_path)
    assert called["start"] >= 1
    settings.get_settings.cache_clear()


def test_get_wifi_service_nmcli_por_omissao(monkeypatch) -> None:
    # Força false: .env local de dev pode ter WIFI_MOCK=true.
    monkeypatch.setenv("WIFI_MOCK", "false")
    settings.get_settings.cache_clear()
    from interface.provision.wifi import NmcliWifiService, get_wifi_service

    assert isinstance(get_wifi_service(), NmcliWifiService)
    settings.get_settings.cache_clear()


def test_get_wifi_service_mock_quando_wifi_mock(monkeypatch) -> None:
    monkeypatch.setenv("WIFI_MOCK", "true")
    settings.get_settings.cache_clear()
    from interface.provision.wifi import MockWifiService, get_wifi_service

    assert isinstance(get_wifi_service(), MockWifiService)
    settings.get_settings.cache_clear()


def test_wifi_fail_nao_persiste_network(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()

    class FailWifi:
        async def connect(self, ssid, password):
            raise RuntimeError("ssid invalido")

    async def run() -> None:
        from interface.provision.wifi import connect_and_persist

        await connect_and_persist("bad", "x", "http://api", "k", service=FailWifi())

    try:
        asyncio.run(run())
        raise AssertionError("esperava RuntimeError")
    except RuntimeError:
        pass
    assert not (tmp_path / "device.json").exists()
    settings.get_settings.cache_clear()


def test_wifi_ok_persiste_network(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()

    class OkWifi:
        async def connect(self, ssid, password):
            return None

    from interface.provision.wifi import connect_and_persist

    async def run() -> None:
        await connect_and_persist(
            "casa",
            "segredo",
            "http://api",
            "k",
            service=OkWifi(),
            stream_ingest_url="rtmps://ingest.example:8443",
        )

    asyncio.run(run())
    data = _read_device(tmp_path)["network"]
    assert data["ssid"] == "casa"
    assert data["password"] == "segredo"
    assert data["stream_ingest_url"] == "rtmps://ingest.example:8443"
    settings.get_settings.cache_clear()


def test_switch_network_falha_nao_persiste(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    _write_device(
        tmp_path,
        {
            "identity": {"device_id": "x"},
            "network": {
                "ssid": "casa",
                "password": "old",
                "api_base_url": "http://api",
                "fiware_api_key": "k",
                "stream_ingest_url": "rtmps://ingest.example:8443",
            },
        },
    )
    restored = {"n": 0}

    class FailThenRestore:
        async def connect(self, ssid, password):
            if ssid == "nova":
                raise RuntimeError("invalida")
            restored["n"] += 1

    async def run() -> None:
        from interface.provision.wifi import switch_network

        ok = await switch_network("nova", "x", service=FailThenRestore())
        assert ok is False

    asyncio.run(run())
    data = _read_device(tmp_path)
    assert data["identity"] == {"device_id": "x"}
    assert data["network"]["ssid"] == "casa"
    assert restored["n"] == 1
    settings.get_settings.cache_clear()


def test_switch_network_ok_persiste(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    _write_device(
        tmp_path,
        {
            "identity": {"device_id": "x"},
            "network": {
                "ssid": "casa",
                "password": "old",
                "api_base_url": "http://api",
                "fiware_api_key": "k",
                "stream_ingest_url": "rtmps://ingest.example:8443",
            },
        },
    )

    class OkWifi:
        async def connect(self, ssid, password):
            return None

    async def run() -> None:
        from interface.provision.wifi import switch_network

        ok = await switch_network("nova", "segredo", service=OkWifi())
        assert ok is True

    asyncio.run(run())
    data = _read_device(tmp_path)
    assert data["identity"] == {"device_id": "x"}
    assert data["network"]["ssid"] == "nova"
    assert data["network"]["password"] == "segredo"
    assert data["network"]["api_base_url"] == "http://api"
    assert data["network"]["stream_ingest_url"] == "rtmps://ingest.example:8443"
    settings.get_settings.cache_clear()


def test_clear_wifi_remove_so_a_rede(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()
    from interface.provision import actions, state as pairing_state

    pairing_state.clear_force_pairing()
    _write_device(
        tmp_path,
        {
            "identity": {"device_id": "x"},
            "network": {"ssid": "casa", "password": "old"},
            "options": {"clips": True},
        },
    )
    monkeypatch.setenv("VIGIA_RESET_WIFI_SCRIPT", str(tmp_path / "missing-script"))
    monkeypatch.setattr(actions, "stop_capture", lambda: None)

    actions.clear_wifi()

    data = _read_device(tmp_path)
    assert data["identity"] == {"device_id": "x"}
    assert "network" not in data
    assert data["options"] == {"clips": True}
    assert identity.is_provisioned() is False
    pairing_state.clear_force_pairing()
    settings.get_settings.cache_clear()


def test_parse_active_ssid() -> None:
    from interface.provision.wifi import _parse_active_ssid

    listing = "no:Outra\nyes:Casa\nno:Vizinho\n"
    assert _parse_active_ssid(listing) == "Casa"
    assert _parse_active_ssid("no:Casa\n") is None


def test_wireless_names_for_ssid() -> None:
    from interface.provision.wifi import _wireless_names_for_ssid

    listing = (
        "Casa:802-11-wireless\n"
        "Casa 1:802-11-wireless\n"
        "Wired connection 1:802-3-ethernet\n"
        "Outra:802-11-wireless\n"
    )
    names = _wireless_names_for_ssid(listing, "Casa")
    assert names == ["Casa", "Casa 1"]
