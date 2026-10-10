"""Testes de options.json (clipes e blur) e do apply no ControlShm."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from shared import options_config as oc
from shared import stream_control as sc


@pytest.fixture
def options_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(oc, "get_options_path", lambda: tmp_path / "options.json")
    monkeypatch.setattr(oc, "get_settings", lambda: SimpleNamespace(blur_video=False))
    return tmp_path


@pytest.fixture
def control_shm(monkeypatch: pytest.MonkeyPatch):
    name = f"voc{uuid.uuid4().hex[:12]}"
    monkeypatch.setattr(
        sc,
        "get_settings",
        lambda: type("S", (), {"stream_control_shm_name": name})(),
    )
    sc.reset_stream_control_for_tests()
    yield name
    sc.reset_stream_control_for_tests()


def test_ausente_clips_desligado_blur_usa_env(
    options_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert oc.clips_enabled() is False
    assert oc.blur_enabled() is False

    monkeypatch.setattr(oc, "get_settings", lambda: SimpleNamespace(blur_video=True))
    assert oc.blur_enabled() is True
    assert not (options_dir / "options.json").exists()


def test_options_invalido_usa_defaults(
    options_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(oc, "get_settings", lambda: SimpleNamespace(blur_video=True))
    path = options_dir / "options.json"
    path.write_text("not-json", encoding="utf-8")
    assert oc.clips_enabled() is False
    assert oc.blur_enabled() is True

    path.write_text(json.dumps(["clips"]), encoding="utf-8")
    assert oc.clips_enabled() is False

    path.write_text(json.dumps({"clips": "yes", "blur": "yes"}), encoding="utf-8")
    assert oc.clips_enabled() is False
    assert oc.blur_enabled() is False


def test_legado_clips_e_blur_enquanto_options_nao_existe(options_dir: Path) -> None:
    (options_dir / "clips.json").write_text(
        json.dumps({"enabled": True}), encoding="utf-8"
    )
    (options_dir / "blur.json").write_text(
        json.dumps({"enabled": True}), encoding="utf-8"
    )
    assert oc.clips_enabled() is True
    assert oc.blur_enabled() is True


def test_save_preserva_a_outra_chave_e_modo(options_dir: Path) -> None:
    oc.save_clips_enabled(True)
    oc.save_blur_enabled(True)
    path = options_dir / "options.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "clips": True,
        "blur": True,
    }
    if os.name == "posix":
        assert path.stat().st_mode & 0o777 == 0o600

    oc.save_clips_enabled(False)
    assert oc.clips_enabled() is False
    assert oc.blur_enabled() is True
    assert json.loads(path.read_text(encoding="utf-8"))["blur"] is True


def test_save_incorpora_legado(options_dir: Path) -> None:
    (options_dir / "clips.json").write_text(
        json.dumps({"enabled": True}), encoding="utf-8"
    )
    oc.save_blur_enabled(True)
    assert json.loads((options_dir / "options.json").read_text(encoding="utf-8")) == {
        "clips": True,
        "blur": True,
    }


def test_apply_nao_reescreve(
    options_dir: Path, control_shm: str
) -> None:
    oc.save_clips_enabled(True)
    oc.save_blur_enabled(True)
    path = options_dir / "options.json"
    written = path.read_bytes()

    oc.apply_persisted_clips()
    oc.apply_persisted_blur()

    assert sc.get_clips_enabled() is True
    assert sc.get_blur_enabled() is True
    assert sc.get_stream_on() is False
    assert path.read_bytes() == written


def test_apply_ausente_preserva_stream(
    options_dir: Path, control_shm: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(oc, "get_settings", lambda: SimpleNamespace(blur_video=True))
    sc.set_stream_status(True)
    oc.apply_persisted_clips()
    oc.apply_persisted_blur()

    assert sc.get_clips_enabled() is False
    assert sc.get_blur_enabled() is True
    assert sc.get_stream_on() is True
    assert not (options_dir / "options.json").exists()
