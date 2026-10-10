"""Testes unitários para shared.settings."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared import settings as st


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    st.get_settings.cache_clear()
    st.get_device_identity.cache_clear()
    st.get_network_settings.cache_clear()
    yield
    st.get_settings.cache_clear()
    st.get_device_identity.cache_clear()
    st.get_network_settings.cache_clear()


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


def test_wifi_mock_segue_debug_quando_ausente(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.delenv("WIFI_MOCK", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    assert st.Settings.from_env().wifi_mock is True

    monkeypatch.setenv("DEBUG", "false")
    assert st.Settings.from_env().wifi_mock is False

    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("WIFI_MOCK", "false")
    assert st.Settings.from_env().wifi_mock is False


def test_from_env_LeVariaveis(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CAPTURE_SOURCE", "1")
    monkeypatch.setenv("SHOW_VIDEO", "true")
    monkeypatch.setenv("SHOW_YOLO_PLOT", "false")
    monkeypatch.setenv("CAPTURE_LOOP", "yes")
    monkeypatch.setenv("YOLO_MODEL", "yolo26n-pose")
    monkeypatch.setenv("FRAME_RATE", "15")
    monkeypatch.setenv("CLASSIFIER", "gru")
    monkeypatch.setenv("SLIDER_WINDOW", "20")
    monkeypatch.setenv("CLIP_WINDOW_S", "30")
    monkeypatch.setenv("DATA_DIR", "/tmp/edge-data")
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)

    cfg = st.Settings.from_env()

    assert cfg.capture_source == 1
    assert cfg.show_video is True
    assert cfg.show_plot is False
    assert cfg.capture_loop is True
    assert cfg.yolo_model == "yolo26n-pose"
    assert cfg.frame_rate == 15
    assert cfg.classifier == "gru"
    assert cfg.slider_window_size == 20
    assert cfg.clip_window_s == 30
    assert cfg.clip_slot_count == 450
    assert cfg.clip_slots_for(30) == 900
    assert cfg.data_dir == "/tmp/edge-data"
    assert st.get_clips_config_path() == Path("/tmp/edge-data/clips.json")
    assert st.get_blur_config_path() == Path("/tmp/edge-data/blur.json")


def test_resolve_ota_dir_DevLocal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.delenv("VIGIA_OTA_DIR", raising=False)
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    st.get_settings.cache_clear()

    assert st.resolve_ota_dir() == tmp_path / "ota"


def test_get_device_identity_SemChaves(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    st.get_settings.cache_clear()
    st.get_device_identity.cache_clear()
    (tmp_path / "identity.json").write_text(
        '{"device_id":"dev-1","device_name":"Vigia-test",'
        '"mac_address":"aa:bb:cc:dd:ee:ff"}',
        encoding="utf-8",
    )

    identity = st.get_device_identity()

    assert identity.device_id == "dev-1"
    assert identity.device_name == "Vigia-test"
    assert not hasattr(identity, "sign_priv")


def test_get_device_identity_Ausente(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    st.get_settings.cache_clear()
    st.get_device_identity.cache_clear()

    with pytest.raises(FileNotFoundError):
        st.get_device_identity()


def test_get_network_settings_CarregaJson(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    st.get_settings.cache_clear()
    st.get_network_settings.cache_clear()

    (tmp_path / "network.json").write_text(
        '{"ssid":"x","password":"y","api_base_url":"http://localhost/vigia",'
        '"fiware_api_key":"k","stream_ingest_url":"rtmp://x"}',
        encoding="utf-8",
    )

    net = st.get_network_settings()
    assert net.fiware_api_key == "k"
    assert net.api_base_url == "http://localhost/vigia"
