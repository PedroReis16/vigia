"""Testes do encaminhamento device_update → pending.json."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from integration import fiware_runner


def test_parse_ultralight_com_valor() -> None:
    parsed = fiware_runner._parse_ultralight_command("dev1@device_update|1.2.3")
    assert parsed == ("dev1", "device_update", "1.2.3")
    parsed = fiware_runner._parse_ultralight_command("dev1@stream_on|")
    assert parsed == ("dev1", "stream_on", "")


def test_on_message_device_update_escreve_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fiware_runner, "OTA_DIR", tmp_path)
    monkeypatch.setattr(fiware_runner, "PENDING_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(
        fiware_runner,
        "get_device_identity",
        lambda: SimpleNamespace(device_id="dev1"),
    )
    msg = MagicMock()
    msg.payload = b"dev1@device_update|4.5.6"
    fiware_runner._on_message(None, None, msg)
    data = json.loads((tmp_path / "pending.json").read_text(encoding="utf-8"))
    assert data["version"] == "4.5.6"
    assert "received_at" in data


def test_on_message_stream_on_nao_escreve_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fiware_runner, "OTA_DIR", tmp_path)
    monkeypatch.setattr(fiware_runner, "PENDING_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(
        fiware_runner,
        "get_device_identity",
        lambda: SimpleNamespace(device_id="dev1"),
    )
    called = {"v": None}
    monkeypatch.setattr(
        fiware_runner, "set_stream_status", lambda v: called.__setitem__("v", v)
    )
    msg = MagicMock()
    msg.payload = b"dev1@stream_on|"
    fiware_runner._on_message(None, None, msg)
    assert called["v"] is True
    assert not (tmp_path / "pending.json").exists()
