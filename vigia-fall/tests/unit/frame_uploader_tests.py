"""Testes unitários para capture.frame_uploader."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np

from capture import frame_uploader


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
    tmp_path,
) -> None:
    (tmp_path / "identity.json").write_text(
        '{"device_id":"dev","device_name":"Vigia-test"}',
        encoding="utf-8",
    )
    (tmp_path / "network.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        frame_uploader, "get_identity_path", lambda: tmp_path / "identity.json"
    )
    monkeypatch.setattr(
        frame_uploader, "get_network_path", lambda: tmp_path / "network.json"
    )

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
