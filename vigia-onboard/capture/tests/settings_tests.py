"""Testes unitários para src.settings."""

from __future__ import annotations

from pathlib import Path

import pytest

from src import settings as st


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    st.get_settings.cache_clear()
    yield
    st.get_settings.cache_clear()


def test_parse_capture_source_IndiceCamera():
    assert st._parse_capture_source("0") == 0
    assert st._parse_capture_source("2") == 2


def test_parse_capture_source_Caminho(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    assert st._parse_capture_source(str(video)) == str(video.resolve())


def test_parse_bool():
    assert st._parse_bool("true") is True
    assert st._parse_bool("1") is True
    assert st._parse_bool("false") is False
    assert st._parse_bool("0") is False


def test_from_env_LeVariaveis(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CAPTURE_SOURCE", "1")
    monkeypatch.setenv("SHOW_VIDEO", "true")
    monkeypatch.setenv("SHOW_YOLO_PLOT", "false")
    monkeypatch.setenv("CAPTURE_LOOP", "yes")
    monkeypatch.setenv("YOLO_MODEL", "yolo26n-pose")
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)

    cfg = st.Settings.from_env()

    assert cfg.capture_source == 1
    assert cfg.show_video is True
    assert cfg.show_yolo_plot is False
    assert cfg.capture_loop is True
    assert cfg.yolo_model == "yolo26n-pose"
