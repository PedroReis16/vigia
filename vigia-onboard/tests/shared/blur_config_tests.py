"""Testes de blur.json e do apply no ControlShm."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from shared import blur_config as bc
from shared import stream_control as sc


@pytest.fixture
def blur_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "blur.json"
    monkeypatch.setattr(bc, "get_blur_config_path", lambda: path)
    return path


@pytest.fixture
def control_shm(monkeypatch: pytest.MonkeyPatch):
    name = f"vbc{uuid.uuid4().hex[:12]}"
    monkeypatch.setattr(
        sc,
        "get_settings",
        lambda: type("S", (), {"stream_control_shm_name": name})(),
    )
    sc.reset_stream_control_for_tests()
    yield name
    sc.reset_stream_control_for_tests()


def test_ausente_usa_blur_video(
    blur_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bc, "get_settings", lambda: SimpleNamespace(blur_video=False))
    assert bc.blur_enabled() is False

    monkeypatch.setattr(bc, "get_settings", lambda: SimpleNamespace(blur_video=True))
    assert bc.blur_enabled() is True
    assert not blur_path.exists()


def test_invalido_vale_desligado(
    blur_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bc, "get_settings", lambda: SimpleNamespace(blur_video=True))

    blur_path.write_text("not-json", encoding="utf-8")
    assert bc.blur_enabled() is False

    blur_path.write_text(json.dumps(["enabled"]), encoding="utf-8")
    assert bc.blur_enabled() is False

    blur_path.write_text(json.dumps({"enabled": "yes"}), encoding="utf-8")
    assert bc.blur_enabled() is False


def test_save_grava_enabled_e_modo(blur_path: Path) -> None:
    bc.save_blur_enabled(True)
    assert json.loads(blur_path.read_text(encoding="utf-8")) == {"enabled": True}
    assert bc.blur_enabled() is True
    if os.name == "posix":
        assert blur_path.stat().st_mode & 0o777 == 0o600

    bc.save_blur_enabled(False)
    assert bc.blur_enabled() is False


def test_apply_liga_shm_sem_reescrever(
    blur_path: Path, control_shm: str
) -> None:
    bc.save_blur_enabled(True)
    written = blur_path.read_bytes()

    bc.apply_persisted_blur()

    assert sc.get_blur_enabled() is True
    assert sc.get_stream_on() is False
    assert sc.get_clips_enabled() is False
    assert blur_path.read_bytes() == written


def test_apply_ausente_usa_env_e_preserva_stream(
    blur_path: Path, control_shm: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bc, "get_settings", lambda: SimpleNamespace(blur_video=True))
    sc.set_stream_status(True)
    bc.apply_persisted_blur()

    assert sc.get_blur_enabled() is True
    assert sc.get_stream_on() is True
    assert not blur_path.exists()
