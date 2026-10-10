"""Testes do loop FIWARE/MQTT e comandos Ultralight no integration."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from integration import integration_runner as runner
from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE
from shared.fall_ipc import normalize_fall_state


def _drain_shm_labels(client: MagicMock, topic: str, labels: list[str]) -> str | None:
    """Simula o poll da fall SHM publicando cada evento enfileirado."""
    ring = EventShmRing.create(slot_count=8, payload_max=64)
    try:
        for label in labels:
            ring.write(EVENT_FALL_STATE, label)
        last: str | None = None
        while True:
            event = ring.read_next(timeout=0.05)
            if event is None:
                break
            state = normalize_fall_state(event.payload)
            runner._publish_fall_state(client, topic, state)
            last = state
        return last
    finally:
        ring.close()
        ring.unlink()


def test_parse_ultralight_com_valor() -> None:
    parsed = runner._parse_ultralight_command("dev1@device_update|1.2.3")
    assert parsed == ("dev1", "device_update", "1.2.3")
    parsed = runner._parse_ultralight_command("dev1@stream_on|")
    assert parsed == ("dev1", "stream_on", "")
    assert runner._parse_ultralight_command("sem-arroba") is None


def test_on_message_device_update_escreve_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "OTA_DIR", tmp_path)
    monkeypatch.setattr(runner, "PENDING_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(runner, "_device_id", "dev1")
    msg = MagicMock()
    msg.payload = b"dev1@device_update|deadbeef"
    runner._on_message(None, None, msg)
    data = json.loads((tmp_path / "pending.json").read_text(encoding="utf-8"))
    assert data["revision"] == "deadbeef"
    assert "received_at" in data


def test_on_message_stream_on_nao_escreve_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "OTA_DIR", tmp_path)
    monkeypatch.setattr(runner, "PENDING_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(runner, "_device_id", "dev1")
    called: dict[str, bool | None] = {"v": None}
    monkeypatch.setattr(
        runner, "set_stream_status", lambda v: called.__setitem__("v", v)
    )
    msg = MagicMock()
    msg.payload = b"dev1@stream_on|"
    runner._on_message(None, None, msg)
    assert called["v"] is True
    assert not (tmp_path / "pending.json").exists()


def test_on_message_clips_on_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "OTA_DIR", tmp_path)
    monkeypatch.setattr(runner, "PENDING_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(runner, "_device_id", "dev1")
    clips_path = tmp_path / "clips.json"
    monkeypatch.setattr(
        "shared.clips_config.get_clips_config_path", lambda: clips_path
    )
    called: dict[str, bool | None] = {"v": None}
    monkeypatch.setattr(
        runner, "set_clips_enabled", lambda v: called.__setitem__("v", v)
    )
    msg = MagicMock()
    msg.payload = b"dev1@clips_on|"
    runner._on_message(None, None, msg)
    assert called["v"] is True
    assert json.loads(clips_path.read_text(encoding="utf-8")) == {"enabled": True}

    msg.payload = b"dev1@clips_off|"
    runner._on_message(None, None, msg)
    assert called["v"] is False
    assert json.loads(clips_path.read_text(encoding="utf-8")) == {"enabled": False}


def test_on_message_blur_on_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "OTA_DIR", tmp_path)
    monkeypatch.setattr(runner, "PENDING_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(runner, "_device_id", "dev1")
    blur_path = tmp_path / "blur.json"
    monkeypatch.setattr(
        "shared.blur_config.get_blur_config_path", lambda: blur_path
    )
    called: dict[str, bool | None] = {"v": None}
    monkeypatch.setattr(
        runner, "set_blur_enabled", lambda v: called.__setitem__("v", v)
    )
    msg = MagicMock()
    msg.payload = b"dev1@blur_on|"
    runner._on_message(None, None, msg)
    assert called["v"] is True
    assert json.loads(blur_path.read_text(encoding="utf-8")) == {"enabled": True}

    msg.payload = b"dev1@blur_off|"
    runner._on_message(None, None, msg)
    assert called["v"] is False
    assert json.loads(blur_path.read_text(encoding="utf-8")) == {"enabled": False}


@pytest.mark.parametrize(
    ("api_base_url", "expected"),
    [
        (
            "https://services.vigiadeteccoes.com.br/vigia",
            ("mosquitto.vigiadeteccoes.com.br", 443, "/", True),
        ),
        (
            "http://host.docker.internal:81/vigia",
            ("host.docker.internal", 81, "/vigia/fiware/mosquitto", False),
        ),
        (
            "http://localhost/vigia",
            ("localhost", 81, "/vigia/fiware/mosquitto", False),
        ),
        (
            "http://localhost:8090/vigia",
            ("localhost", 81, "/vigia/fiware/mosquitto", False),
        ),
    ],
)
def test_mqtt_endpoint(api_base_url: str, expected: tuple) -> None:
    assert runner._mqtt_endpoint(api_base_url) == expected


def test_fiware_loop_publica_cada_evento_da_shm() -> None:
    client = MagicMock()
    last = _drain_shm_labels(
        client,
        "/key/dev/attrs",
        ["NORMAL", "NORMAL", "SUSPECT", "SUSPECT", "FALL", "FALL"],
    )

    assert last == "fall"
    assert client.publish.call_args_list == [
        (("/key/dev/attrs", "fall|normal"),),
        (("/key/dev/attrs", "fall|normal"),),
        (("/key/dev/attrs", "fall|suspect"),),
        (("/key/dev/attrs", "fall|suspect"),),
        (("/key/dev/attrs", "fall|fall"),),
        (("/key/dev/attrs", "fall|fall"),),
    ]


def test_fiware_loop_normaliza_aliases_por_evento() -> None:
    client = MagicMock()
    last = _drain_shm_labels(client, "/t", ["NORMAL", "ADL", "ok"])

    assert last == "normal"
    assert client.publish.call_args_list == [
        (("/t", "fall|normal"),),
        (("/t", "fall|normal"),),
        (("/t", "fall|normal"),),
    ]


def test_run_integration_EsperaProvisionamento(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps = {"n": 0}

    def _missing():
        raise FileNotFoundError("Identity file not found")

    def _sleep(_seconds: float) -> None:
        sleeps["n"] += 1
        if sleeps["n"] >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(runner, "get_device_identity", _missing)
    monkeypatch.setattr(runner.time, "sleep", _sleep)
    with pytest.raises(KeyboardInterrupt):
        runner.run_integration()
    assert sleeps["n"] >= 1


def test_run_integration_PublicaEventosDaShm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cliente MQTT mockado; um evento SHM → publish; depois KeyboardInterrupt."""
    ring = EventShmRing.create(slot_count=4, payload_max=64)
    ring.write(EVENT_FALL_STATE, "suspect")

    client = MagicMock()
    connect_calls = {"n": 0}

    def fake_connect(*_a, **_k):
        connect_calls["n"] += 1

    client.connect.side_effect = fake_connect
    client.loop_start = MagicMock()
    client.loop_stop = MagicMock()
    client.disconnect = MagicMock()

    read_count = {"n": 0}
    original_read = ring.read_next

    def read_then_interrupt(timeout: float = 0.05):
        read_count["n"] += 1
        if read_count["n"] == 1:
            return original_read(timeout=timeout)
        raise KeyboardInterrupt

    monkeypatch.setattr(
        runner,
        "get_device_identity",
        lambda: SimpleNamespace(device_id="dev1"),
    )
    monkeypatch.setattr(
        runner,
        "get_network_settings",
        lambda: SimpleNamespace(
            api_base_url="http://localhost/vigia",
            fiware_api_key="apikey",
        ),
    )
    monkeypatch.setattr(runner, "resolve_ota_dir", lambda: Path("/tmp/ota-test"))
    monkeypatch.setattr(runner, "apply_persisted_clips", lambda: None)
    monkeypatch.setattr(runner, "apply_persisted_blur", lambda: None)
    monkeypatch.setattr(runner, "_create_mqtt_client", lambda *_a, **_k: client)
    monkeypatch.setattr(runner, "attach_fall_shm", lambda: ring)
    monkeypatch.setattr(runner, "capture_allowed", lambda: True)
    monkeypatch.setattr(ring, "read_next", read_then_interrupt)

    try:
        runner.run_integration()
    finally:
        ring.close()
        ring.unlink()

    assert connect_calls["n"] == 1
    client.publish.assert_called_once_with("/apikey/dev1/attrs", "fall|suspect")
    client.loop_stop.assert_called_once()
    client.disconnect.assert_called_once()


def test_run_integration_NaoPublicaComGateFechado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    ring = EventShmRing.create(slot_count=4, payload_max=64)
    sleeps = {"n": 0}

    def _sleep(_seconds: float) -> None:
        sleeps["n"] += 1
        if sleeps["n"] >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(
        runner,
        "get_device_identity",
        lambda: SimpleNamespace(device_id="dev1"),
    )
    monkeypatch.setattr(
        runner,
        "get_network_settings",
        lambda: SimpleNamespace(
            api_base_url="http://localhost/vigia",
            fiware_api_key="apikey",
        ),
    )
    monkeypatch.setattr(runner, "resolve_ota_dir", lambda: Path("/tmp/ota-test"))
    monkeypatch.setattr(runner, "apply_persisted_clips", lambda: None)
    monkeypatch.setattr(runner, "apply_persisted_blur", lambda: None)
    monkeypatch.setattr(runner, "_create_mqtt_client", lambda *_a, **_k: client)
    monkeypatch.setattr(runner, "attach_fall_shm", lambda: ring)
    monkeypatch.setattr(runner, "capture_allowed", lambda: False)
    monkeypatch.setattr(runner.time, "sleep", _sleep)

    try:
        runner.run_integration()
    finally:
        ring.close()
        ring.unlink()

    client.publish.assert_not_called()
    assert sleeps["n"] >= 1
