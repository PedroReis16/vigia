"""Testes dos runners de stream/clips e supervisor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import stream as stream_pkg
from shared.live_frame_shm import LiveFrameShm
from stream import clips_runner, stream_runner
from stream.rtmp import reset_rtmp_for_tests


@pytest.fixture(autouse=True)
def _reset_workers():
    stream_pkg.stop_all_workers(join_timeout=0.5)
    reset_rtmp_for_tests()
    yield
    stream_pkg.stop_all_workers(join_timeout=0.5)
    reset_rtmp_for_tests()


def test_stream_runner_PublicaEnquantoStreamOn() -> None:
    live = LiveFrameShm.create(max_payload=64)
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    live.write(frame, 12)

    calls = {"n": 0}

    def on_then_off():
        calls["n"] += 1
        return calls["n"] <= 1

    try:
        with (
            patch.object(stream_runner, "get_stream_on", side_effect=on_then_off),
            patch.object(stream_runner, "publish_frame") as publish,
            patch.object(stream_runner, "shutdown_stream") as shutdown,
        ):
            stream_runner.run_stream_worker(live.name)

        publish.assert_called_once()
        np.testing.assert_array_equal(publish.call_args[0][0], frame)
        assert publish.call_args[0][1] == 12
        shutdown.assert_called_once()
    finally:
        live.close()
        live.unlink()


def test_clip_frame_size_Reduz1080pParaCabarNoRing() -> None:
    height, width = clips_runner.clip_frame_size(1080, 1920, 3, 640 * 480 * 3)
    assert height * width * 3 <= 640 * 480 * 3
    assert height < 1080
    assert width < 1920
    assert abs((width / height) - (1920 / 1080)) < 0.05


def test_fit_frame_to_payload_MantemFrameQueCabe() -> None:
    frame = np.full((2, 2, 3), 7, dtype=np.uint8)
    fitted = clips_runner.fit_frame_to_payload(frame, 64)
    np.testing.assert_array_equal(fitted, frame)


def test_encode_clip_jpeg_BaixaQualidadeSoSeNaoCabir() -> None:
    frame = np.zeros((8, 8, 3), dtype=np.uint8)
    seen: list[int] = []

    def imencode(_ext, image, params):
        assert image.shape == frame.shape
        quality = int(params[1])
        seen.append(quality)
        payload = b"a" * (10 if quality < 100 else 50)
        return True, np.frombuffer(payload, dtype=np.uint8)

    import cv2

    cv2.imencode = imencode
    encoded = clips_runner.encode_clip_jpeg(frame, 20)
    assert seen[0] == 100
    assert encoded == b"a" * 10


def test_store_clip_frame_JpegNaResolucaoOriginal() -> None:
    frame = np.zeros((8, 8, 3), dtype=np.uint8)
    ring = MagicMock()
    ring.max_payload = 32
    with patch.object(clips_runner, "encode_clip_jpeg", return_value=b"jpeg"):
        clips_runner._store_clip_frame(ring, frame)
    ring.push.assert_not_called()
    ring.push_jpeg.assert_called_once_with(b"jpeg", 8, 8, capture_ts=ring.push_jpeg.call_args.kwargs["capture_ts"])


def test_resolve_clip_fps_PrefereCamera():
    assert clips_runner._resolve_clip_fps(30, 12) == 30
    assert clips_runner._resolve_clip_fps(None, 12) == 12
    assert clips_runner._resolve_clip_fps(0, 12) == 12


def test_clips_runner_JanelaEExportNoFpsDaCamera() -> None:
    live = LiveFrameShm.create(max_payload=64)
    frame = np.full((2, 2, 3), 3, dtype=np.uint8)
    live.write(frame, 30)
    clip = MagicMock()
    clip.__len__.return_value = 1
    stored = MagicMock()
    stored.frame = frame
    clip.snapshot.return_value = [stored]
    calls = {"n": 0}
    exported: dict[str, int] = {}

    def on_then_off():
        calls["n"] += 1
        return calls["n"] <= 1

    def capture_export(frames, fps):
        exported["fps"] = fps
        exported["n"] = len(frames)

    class _ImmediateThread:
        def __init__(self, target, args, **kwargs):
            self._target = target
            self._args = args

        def start(self) -> None:
            self._target(*self._args)

        def is_alive(self) -> bool:
            return False

    try:
        with (
            patch.object(clips_runner, "get_clips_enabled", side_effect=on_then_off),
            patch.object(clips_runner, "get_settings") as settings,
            patch.object(clips_runner, "_latest_fall_state", return_value="fall"),
            patch.object(clips_runner, "_export_snapshot", side_effect=capture_export),
            patch.object(clips_runner.threading, "Thread", _ImmediateThread),
            patch.object(
                clips_runner.ClipFrameRing,
                "open_or_create",
                return_value=clip,
            ) as open_ring,
        ):
            settings.return_value = MagicMock(
                clip_shm_name="clip-test",
                clip_max_payload=64,
                frame_rate=12,
                fall_shm_name="fall-test",
                clip_window_s=30,
            )
            settings.return_value.clip_slots_for.side_effect = lambda fps: 30 * int(fps)
            clips_runner.run_clips_worker(live.name, "clip-test", None, 30)

        assert open_ring.call_args.kwargs["slot_count"] == 900
        assert exported["fps"] == 30
        assert exported["n"] == 1
    finally:
        live.close()
        live.unlink()


def test_clips_runner_EmpilhaNaJanela() -> None:
    live = LiveFrameShm.create(max_payload=64)
    frame = np.full((2, 2, 3), 7, dtype=np.uint8)
    live.write(frame, 12)

    clip = MagicMock()
    calls = {"n": 0}

    def on_then_off():
        calls["n"] += 1
        return calls["n"] <= 1

    try:
        with (
            patch.object(clips_runner, "get_clips_enabled", side_effect=on_then_off),
            patch.object(clips_runner, "get_settings") as settings,
            patch.object(
                clips_runner.ClipFrameRing,
                "open_or_create",
                return_value=clip,
            ),
        ):
            settings.return_value = MagicMock(
                clip_shm_name="clip-test",
                clip_max_payload=64,
                frame_rate=12,
                fall_shm_name="fall-test",
            )
            settings.return_value.clip_slots_for.return_value = 4
            clips_runner.run_clips_worker(live.name, "clip-test")

        clip.push.assert_called_once()
        np.testing.assert_array_equal(clip.push.call_args[0][0], frame)
        clip.close.assert_called_once()
    finally:
        live.close()
        live.unlink()


def test_supervise_workers_SobeEParaIndependentes() -> None:
    live = MagicMock()
    live.name = "live"

    with (
        patch.object(stream_pkg, "ensure_stream_worker") as ensure_stream,
        patch.object(stream_pkg, "ensure_clips_worker") as ensure_clips,
        patch.object(stream_pkg, "ensure_thumbs_worker") as ensure_thumbs,
        patch.object(stream_pkg, "stop_stream_worker") as stop_stream,
        patch.object(stream_pkg, "stop_clips_worker") as stop_clips,
    ):
        stream_pkg._stream_task = None
        stream_pkg._clips_task = None
        stream_pkg._thumbs_task = None

        stream_pkg.supervise_workers(
            "live",
            stream_on=True,
            clips_enabled=False,
            live_shm=live,
        )
        ensure_stream.assert_called_once_with("live")
        ensure_clips.assert_not_called()
        ensure_thumbs.assert_called_once_with("live")
        assert stream_pkg.export_active() is True

        fake_stream = MagicMock()
        fake_stream.is_alive.return_value = True
        stream_pkg._stream_task = fake_stream

        stream_pkg.supervise_workers(
            "live",
            stream_on=False,
            clips_enabled=True,
            clip_shm_name="clip",
            live_shm=live,
        )
        stop_stream.assert_called_once()
        ensure_clips.assert_called_once_with("live", "clip", capture_fps=None)
        stop_clips.assert_not_called()

        stream_pkg._clips_task = None
        stream_pkg.supervise_workers(
            "live",
            stream_on=False,
            clips_enabled=True,
            clip_shm_name="clip",
            live_shm=live,
            capture_fps=30,
        )
        ensure_clips.assert_called_with("live", "clip", capture_fps=30)
