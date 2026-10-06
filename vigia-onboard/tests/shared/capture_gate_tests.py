"""Gate em ficheiro da captura."""

from __future__ import annotations

import os

import pytest

from shared import capture_gate as gate
from shared import settings as st


@pytest.fixture(autouse=True)
def _data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    st.get_settings.cache_clear()
    yield tmp_path
    st.get_settings.cache_clear()


def test_capture_allowed_ExigeIdentityNetworkESemHold(tmp_path):
    assert gate.capture_allowed() is False
    (tmp_path / "identity.json").write_text("{}", encoding="utf-8")
    assert gate.capture_allowed() is False
    (tmp_path / "network.json").write_text("{}", encoding="utf-8")
    assert gate.capture_allowed() is True
    gate.hold_capture()
    assert gate.capture_allowed() is False
    gate.release_capture()
    assert gate.capture_allowed() is True


def test_restart_E_pid(tmp_path):
    assert gate.restart_pending() is False
    gate.request_capture_restart()
    assert gate.restart_pending() is True
    assert gate.consume_capture_restart() is True
    assert gate.restart_pending() is False

    gate.write_capture_pid(os.getpid())
    assert gate.read_capture_pid() == os.getpid()
    assert gate.capture_is_active() is True
    gate.clear_capture_pid()
    assert gate.read_capture_pid() is None
    assert gate.capture_is_active() is False
