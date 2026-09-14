"""Testes para alinhamento DEBUG da identity com TestDeviceSeed."""

from __future__ import annotations

import json
from pathlib import Path

from shared import get_device_identity, get_settings, test_device_seed


def test_get_device_identity_EmDebugComDeviceSeed_AlinhaSignPriv(
    monkeypatch, tmp_path: Path
) -> None:
    identity_path = tmp_path / "identity.json"
    identity_path.write_text(
        json.dumps(
            {
                "device_id": test_device_seed.DEVICE_ID,
                "device_name": "Vigia-test",
                "sign_priv": "aa" * 32,
                "ecdh_priv": "bb" * 32,
            }
        )
    )

    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    get_device_identity.cache_clear()

    identity = get_device_identity()

    assert identity.sign_priv == test_device_seed.SIGN_PRIVATE_KEY
    saved = json.loads(identity_path.read_text())
    assert saved["sign_priv"] == test_device_seed.SIGN_PRIVATE_KEY


def test_get_device_identity_SemDebug_NaoAlinhaSignPriv(
    monkeypatch, tmp_path: Path
) -> None:
    wrong_priv = "cc" * 32
    identity_path = tmp_path / "identity.json"
    identity_path.write_text(
        json.dumps(
            {
                "device_id": test_device_seed.DEVICE_ID,
                "device_name": "Vigia-test",
                "sign_priv": wrong_priv,
                "ecdh_priv": "dd" * 32,
            }
        )
    )

    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    get_device_identity.cache_clear()

    identity = get_device_identity()

    assert identity.sign_priv == wrong_priv
