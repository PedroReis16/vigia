"""Testes de leitura de identity.json."""

from __future__ import annotations

import json
from pathlib import Path

from shared import get_device_identity, get_settings


def test_get_device_identity_IgnoraChavesLegadas(monkeypatch, tmp_path: Path) -> None:
    identity_path = tmp_path / "identity.json"
    identity_path.write_text(
        json.dumps(
            {
                "device_id": "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c",
                "device_name": "Vigia-test",
                "sign_priv": "aa" * 32,
                "ecdh_priv": "bb" * 32,
            }
        )
    )

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    get_device_identity.cache_clear()

    identity = get_device_identity()

    assert identity.device_id == "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"
    assert identity.device_name == "Vigia-test"
    assert not hasattr(identity, "sign_priv")
