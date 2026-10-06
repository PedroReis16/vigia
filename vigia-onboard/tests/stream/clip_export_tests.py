"""Decisão de exportar o clipe na entrada em queda."""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np

from stream import clip_export


def test_entrada_em_fall_exporta_uma_vez() -> None:
    export, episode = clip_export.next_clip_export(False, "normal", 10, False)
    assert (export, episode) == (False, False)

    export, episode = clip_export.next_clip_export(False, "fall", 10, False)
    assert (export, episode) == (True, True)

    export, episode = clip_export.next_clip_export(True, "FALL", 10, False)
    assert (export, episode) == (False, True)


def test_sair_de_fall_permite_novo_clipe() -> None:
    _, episode = clip_export.next_clip_export(False, "fall", 4, False)
    export, episode = clip_export.next_clip_export(episode, "normal", 4, False)
    assert (export, episode) == (False, False)

    export, episode = clip_export.next_clip_export(episode, "fall", 4, False)
    assert (export, episode) == (True, True)


def test_ring_vazio_nao_exporta() -> None:
    assert clip_export.next_clip_export(False, "fall", 0, False) == (False, False)


def test_upload_clip_nao_envia_assinatura(tmp_path: Path) -> None:
    frame = tmp_path / "000000.png"
    frame.write_bytes(b"\x89PNG\r\n\x1a\n")
    calls: list[object] = []

    def opener(request, timeout):  # noqa: ANN001
        calls.append(request)
        response = MagicMock()
        response.status = 202
        return response

    clip_export.upload_clip(
        "http://localhost:8090/vigia",
        "ca2e7b82-2c24-4f48-918d-6b715db681ba",
        "11111111-1111-1111-1111-111111111111",
        12,
        [frame],
        opener=opener,
    )

    assert len(calls) == 2
    session = calls[0]
    frame_request = calls[1]
    assert session.get_full_url().endswith(
        "/devices/ca2e7b82-2c24-4f48-918d-6b715db681ba/clips"
    )
    assert frame_request.get_full_url().endswith("/frames/0")
    assert session.get_header("X-device-signature") is None
    assert session.get_header("Content-type") == "application/json"
    assert frame_request.get_header("Content-type") == "image/png"


def test_upload_clip_envia_frames_em_paralelo(tmp_path: Path) -> None:
    frames = []
    for index in range(3):
        path = tmp_path / f"{index:06d}.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        frames.append(path)

    seen: list[str] = []
    lock = threading.Lock()

    def opener(request, timeout):  # noqa: ANN001
        with lock:
            seen.append(request.get_full_url())
        response = MagicMock()
        response.status = 202
        return response

    clip_export.upload_clip(
        "http://localhost:8090/vigia",
        "ca2e7b82-2c24-4f48-918d-6b715db681ba",
        "11111111-1111-1111-1111-111111111111",
        30,
        frames,
        opener=opener,
    )

    assert seen[0].endswith("/devices/ca2e7b82-2c24-4f48-918d-6b715db681ba/clips")
    assert {url.rsplit("/", 1)[-1] for url in seen[1:]} == {"0", "1", "2"}


def test_encode_frames_as_png_pede_png_sem_perdas(tmp_path: Path, monkeypatch) -> None:
    def fake_run(command, **kwargs):  # noqa: ANN001
        Path(command[-1].replace("%06d", "000000")).write_bytes(b"png")
        completed = MagicMock()
        completed.returncode = 0
        completed.stderr = b""
        fake_run.command = command
        return completed

    monkeypatch.setattr(clip_export.subprocess, "run", fake_run)
    frames = [np.zeros((2, 3, 3), dtype=np.uint8)]
    paths = clip_export.encode_frames_as_png(frames, tmp_path)

    command = fake_run.command
    assert "bgr24" in command
    assert command[-1].endswith("%06d.png")
    assert paths == [tmp_path / "000000.png"]
