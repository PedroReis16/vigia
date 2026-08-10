"""Testes unitários para capture.frame_uploader."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock

import numpy as np
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from capture import frame_uploader
from shared import test_device_seed


def test_build_multipart_ContemJpegEBoundary() -> None:
    jpeg = b"\xff\xd8\xff\xd9"
    body, content_type = frame_uploader._build_multipart(jpeg)

    assert "multipart/form-data; boundary=" in content_type
    assert b"Content-Disposition: form-data; name=\"frameFile\"" in body
    assert b"Content-Type: image/jpeg" in body
    assert jpeg in body
    assert body.endswith(b"--\r\n")


def test_normalize_api_base_GaranteBarraFinal() -> None:
    assert frame_uploader._normalize_api_base("http://localhost:8090/vigia") == (
        "http://localhost:8090/vigia/"
    )
    assert frame_uploader._normalize_api_base("http://localhost:8090/vigia/") == (
        "http://localhost:8090/vigia/"
    )


def test_device_signature_Canonical_VerificaComChavePublicaDoSeed() -> None:
    """Espelha DeviceSignatureAuthenticationHandler + TestDeviceSeed."""
    jpeg = b"\xff\xd8\xff\xd9"
    body, _ = frame_uploader._build_multipart(jpeg)
    timestamp = 1_720_000_000
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = (
        f"POST\n/devices/{test_device_seed.DEVICE_ID}/frame\n"
        f"{timestamp}\n{body_hash}"
    )

    private_key = Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(test_device_seed.SIGN_PRIVATE_KEY)
    )
    signature = private_key.sign(canonical.encode("utf-8"))

    public_key = Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(test_device_seed.SIGN_PUBLIC_KEY)
    )
    public_key.verify(signature, canonical.encode("utf-8"))


def test_maybe_upload_thumbnail_ComFrameVazio_NaoDisparaUpload(
    monkeypatch,
) -> None:
    started = []

    monkeypatch.setattr(
        frame_uploader.threading,
        "Thread",
        lambda *args, **kwargs: started.append(True) or MagicMock(),
    )

    frame_uploader.maybe_upload_thumbnail(np.zeros((0, 0, 3), dtype=np.uint8))

    assert started == []


def test_maybe_upload_thumbnail_ComIntervaloRespeitado_DisparaUmaVez(
    monkeypatch,
) -> None:
    started: list[MagicMock] = []

    class FakeThread:
        def __init__(self, *args, **kwargs) -> None:
            started.append(MagicMock())
            self._target = kwargs.get("target") or (args[0] if args else None)
            self._args = kwargs.get("args") or ()

        def start(self) -> None:
            # Não executa o worker de verdade nos testes.
            return None

    monkeypatch.setattr(frame_uploader.threading, "Thread", FakeThread)
    monkeypatch.setattr(frame_uploader, "_last_upload_monotonic", 0.0)
    monkeypatch.setattr(frame_uploader, "_upload_in_flight", False)
    monkeypatch.setattr(frame_uploader.time, "monotonic", lambda: 1000.0)

    frame = np.zeros((8, 8, 3), dtype=np.uint8)
    frame_uploader.maybe_upload_thumbnail(frame)
    frame_uploader.maybe_upload_thumbnail(frame)

    assert len(started) == 1
