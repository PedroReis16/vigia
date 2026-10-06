"""Testes de clips.json e do apply no ControlShm."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest

from shared import clips_config as cc
from shared import stream_control as sc


@pytest.fixture
def clips_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "clips.json"
    monkeypatch.setattr(cc, "get_clips_config_path", lambda: path)
    return path


@pytest.fixture
def control_shm(monkeypatch: pytest.MonkeyPatch):
    name = f"vcc{uuid.uuid4().hex[:12]}"
    monkeypatch.setattr(
        sc,
        "get_settings",
        lambda: type("S", (), {"stream_control_shm_name": name})(),
    )
    sc.reset_stream_control_for_tests()
    yield name
    sc.reset_stream_control_for_tests()


def test_ausente_ou_invalido_vale_desligado(clips_path: Path) -> None:
    assert cc.clips_enabled() is False

    clips_path.write_text("not-json", encoding="utf-8")
    assert cc.clips_enabled() is False

    clips_path.write_text(json.dumps(["enabled"]), encoding="utf-8")
    assert cc.clips_enabled() is False

    clips_path.write_text(json.dumps({"enabled": "yes"}), encoding="utf-8")
    assert cc.clips_enabled() is False


def test_save_grava_enabled_e_modo(clips_path: Path) -> None:
    cc.save_clips_enabled(True)
    assert json.loads(clips_path.read_text(encoding="utf-8")) == {"enabled": True}
    assert cc.clips_enabled() is True
    if os.name == "posix":
        assert clips_path.stat().st_mode & 0o777 == 0o600

    cc.save_clips_enabled(False)
    assert cc.clips_enabled() is False


def test_apply_liga_shm_sem_comando(clips_path: Path, control_shm: str) -> None:
    cc.save_clips_enabled(True)
    written = clips_path.read_bytes()

    cc.apply_persisted_clips()

    assert sc.get_clips_enabled() is True
    assert sc.get_stream_on() is False
    assert clips_path.read_bytes() == written


def test_apply_ausente_deixa_clips_desligados(clips_path: Path, control_shm: str) -> None:
    sc.set_stream_status(True)
    cc.apply_persisted_clips()

    assert sc.get_clips_enabled() is False
    assert sc.get_stream_on() is True
    assert not clips_path.exists()
