"""Testes unitários para stream.frame_uploader."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np

from stream import frame_uploader


def test_build_multipart_ContemJpegEBoundary() -> None:
    jpeg = b"\xff\xd8\xff\xd9"
    body, content_type = frame_uploader._build_multipart(jpeg)

    assert "multipart/form-data; boundary=" in content_type
    assert b'Content-Disposition: form-data; name="frameFile"' in body
    assert b"Content-Type: image/jpeg" in body
    assert jpeg in body
    assert body.endswith(b"--\r\n")


def test_normalize_api_base_GaranteBarraFinal() -> None:
    assert frame_uploader._normalize_api_base("http://10.0.0.51:8090/vigia") == (
        "http://10.0.0.51:8090/vigia/"
    )
    assert frame_uploader._normalize_api_base("http://10.0.0.51:8090/vigia/") == (
        "http://10.0.0.51:8090/vigia/"
    )


def test_upload_thumbnail_ComFrameVazio_NaoEnvia(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(
        frame_uploader,
        "_post_frame",
        lambda *args: called.append(args),
    )

    assert frame_uploader.upload_thumbnail(np.zeros((0, 0, 3), dtype=np.uint8)) is False
    assert called == []


def test_upload_thumbnail_posta_jpeg_sem_assinatura(monkeypatch) -> None:
    calls: list[object] = []

    def opener(request, timeout):  # noqa: ANN001
        calls.append(request)
        response = MagicMock()
        response.status = 202
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        return response

    monkeypatch.setattr(frame_uploader, "urlopen", opener)
    monkeypatch.setattr(
        frame_uploader,
        "get_identity_path",
        lambda: MagicMock(exists=lambda: True),
    )
    monkeypatch.setattr(
        frame_uploader,
        "get_network_path",
        lambda: MagicMock(exists=lambda: True),
    )
    monkeypatch.setattr(
        frame_uploader,
        "get_device_identity",
        lambda: SimpleNamespace(device_id="ca2e7b82-2c24-4f48-918d-6b715db681ba"),
    )
    monkeypatch.setattr(
        frame_uploader,
        "get_network_settings",
        lambda: SimpleNamespace(api_base_url="http://localhost:8090/vigia"),
    )
    monkeypatch.setattr(
        frame_uploader.cv2,
        "imencode",
        lambda *_args, **_kwargs: (True, np.array([0xFF, 0xD8, 0xFF, 0xD9], dtype=np.uint8)),
    )

    assert frame_uploader.upload_thumbnail(np.zeros((4, 4, 3), dtype=np.uint8)) is True

    assert len(calls) == 1
    request = calls[0]
    assert request.get_full_url().endswith(
        "/devices/ca2e7b82-2c24-4f48-918d-6b715db681ba/frame"
    )
    assert request.get_method() == "POST"
    assert request.get_header("X-device-signature") is None
    assert "multipart/form-data" in request.get_header("Content-type")
