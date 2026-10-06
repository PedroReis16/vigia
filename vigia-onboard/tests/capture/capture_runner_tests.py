"""Testes unitários para capture.capture_runner."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from capture import capture_runner as cr


def _settings(**overrides) -> SimpleNamespace:
    values = {
        "capture_source": 0,
        "show_video": False,
        "show_plot": False,
        "blur_video": False,
        "capture_loop": False,
        "yolo_model": "yolo26s-pose",
        "frame_rate": 12,
        "live_shm_name": "vigia-onboard-live-test",
        "clip_shm_name": "vigia-onboard-clip-test",
        "clip_max_payload": 640 * 480 * 3,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _result(frame: str = "frame") -> MagicMock:
    result = MagicMock()
    result.orig_img = frame
    result.keypoints = None
    result.boxes = None
    result.plot.return_value = frame
    return result


@pytest.fixture
def capture_deps():
    cap = MagicMock()
    cap.isOpened.return_value = True
    cv2 = MagicMock()
    cv2.VideoCapture.return_value = cap
    cv2.waitKey.return_value = 0
    model = MagicMock()

    with (
        patch.object(cr, "get_yolo_model", return_value=model),
        patch.object(cr, "cv2", cv2),
        patch.object(cr, "start_core_worker"),
        patch.object(cr, "stop_core_worker"),
        patch.object(cr, "save_points"),
        patch.object(cr, "unpack_raw_points", return_value=[]),
        patch.object(cr, "prepare_multiprocessing"),
        patch.object(cr, "apply_persisted_clips"),
        patch.object(cr, "start_supervisor"),
        patch.object(cr, "stop_supervisor"),
        patch.object(cr, "export_active", return_value=False),
        patch.object(cr, "_open_live_shm", return_value=None),
        patch.object(cr, "capture_allowed", return_value=True),
        patch.object(cr, "restart_pending", return_value=False),
        patch.object(cr, "write_capture_pid"),
        patch.object(cr, "clear_capture_pid"),
        patch.object(cr, "consume_capture_restart"),
    ):
        yield SimpleNamespace(
            cap=cap,
            cv2=cv2,
            model=model,
        )


def test_source_label_CameraEVideo():
    assert cr._source_label(0) == "câmera 0"
    assert "clip.mp4" in cr._source_label("/tmp/clip.mp4")


def test_source_fps_UsaFonteOuFrameRate():
    cap = MagicMock()
    cap.get.return_value = 29.97
    assert cr._source_fps(cap, 12) == 30

    cap.get.return_value = 0
    assert cr._source_fps(cap, 12) == 12

    cap.get.side_effect = TypeError
    assert cr._source_fps(cap, 12) == 12


def test_should_restart_stream_SoArquivoComLoopEFrames():
    assert cr._should_restart_stream("/tmp/clip.mp4", True, True, False)
    assert not cr._should_restart_stream(0, True, True, False)
    assert not cr._should_restart_stream("/tmp/clip.mp4", False, True, False)
    assert not cr._should_restart_stream("/tmp/clip.mp4", True, False, False)
    assert not cr._should_restart_stream("/tmp/clip.mp4", True, True, True)


def test_run_capture_GateFechado_NaoAbreCamera(capture_deps, monkeypatch):
    monkeypatch.setattr(cr, "capture_allowed", lambda: False)

    def _sleep(_seconds: float) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cr.time, "sleep", _sleep)
    with pytest.raises(KeyboardInterrupt):
        cr.run_capture()
    capture_deps.model.track.assert_not_called()


def test_run_capture_Restart_AbreNovaSessao(capture_deps, monkeypatch):
    flag = {"on": False}
    monkeypatch.setattr(cr, "restart_pending", lambda: flag["on"])

    def _consume() -> bool:
        flag["on"] = False
        return True

    monkeypatch.setattr(cr, "consume_capture_restart", _consume)

    saves = {"n": 0}

    def _save(_points) -> None:
        saves["n"] += 1
        if saves["n"] == 1:
            flag["on"] = True

    monkeypatch.setattr(cr, "save_points", _save)
    capture_deps.model.track.side_effect = [iter([_result("a")]), iter([_result("b")])]

    cr.run_capture()

    assert capture_deps.model.track.call_count == 2


def test_run_capture_FonteFechada_Levanta(capture_deps):
    capture_deps.cap.isOpened.return_value = False

    with patch.object(cr, "get_settings", return_value=_settings()):
        with pytest.raises(ValueError, match="fonte de captura"):
            cr.run_capture()

    capture_deps.cap.release.assert_called_once()
    capture_deps.model.track.assert_not_called()


def test_run_capture_UmFrame_StreamEEncerra(capture_deps):
    result = _result()
    capture_deps.model.track.return_value = iter([result])
    points = [object()]

    with (
        patch.object(cr, "get_settings", return_value=_settings()),
        patch.object(cr, "unpack_raw_points", return_value=points) as unpack,
        patch.object(cr, "save_points") as save,
        patch.object(cr, "start_core_worker") as start,
        patch.object(cr, "stop_core_worker") as stop,
    ):
        cr.run_capture()

    unpack.assert_called_once_with(result)
    save.assert_called_once_with(points)
    start.assert_called_once()
    stop.assert_called_once()
    capture_deps.model.track.assert_called_once_with(
        0, **cr._YOLO_STREAM_KWARGS
    )
    assert cr._YOLO_STREAM_KWARGS["stream"] is True
    assert cr._YOLO_STREAM_KWARGS["persist"] is True
    capture_deps.model.predict.assert_not_called()
    capture_deps.cap.release.assert_called_once()


def test_run_capture_ArquivoComLoop_ReiniciaStream(capture_deps):
    first = _result("a")
    capture_deps.model.track.side_effect = [iter([first]), iter([])]

    with patch.object(
        cr,
        "get_settings",
        return_value=_settings(capture_source="/tmp/clip.mp4", capture_loop=True),
    ):
        cr.run_capture()

    assert capture_deps.model.track.call_count == 2
    capture_deps.model.track.assert_called_with(
        "/tmp/clip.mp4", **cr._YOLO_STREAM_KWARGS
    )


def test_run_capture_CameraNaoReiniciaStream(capture_deps):
    capture_deps.model.track.return_value = iter([_result()])

    with patch.object(
        cr, "get_settings", return_value=_settings(capture_loop=True)
    ):
        cr.run_capture()

    capture_deps.model.track.assert_called_once()


def test_blur_boxes_SemDetecao_DevolveCopia():
    image = MagicMock()
    preview = MagicMock()
    image.copy.return_value = preview

    assert cr._blur_boxes(image, SimpleNamespace(boxes=None)) is preview


def test_blur_boxes_AplicaNasBoxes():
    roi = MagicMock()
    roi.size = 10
    preview = MagicMock()
    preview.shape = (100, 80, 3)
    preview.__getitem__.return_value = roi
    image = MagicMock()
    image.copy.return_value = preview
    result = SimpleNamespace(boxes=SimpleNamespace(xyxy=[[10, 20, 40, 60]]))

    with patch.object(cr, "cv2") as cv2:
        assert cr._blur_boxes(image, result, ksize=51) is preview
        preview.__setitem__.assert_called_once()
        cv2.blur.assert_called_once_with(roi, (51, 51))


def test_run_capture_ShowVideo_BlurEPlot(capture_deps):
    plotted = object()
    result = _result()
    result.plot.return_value = plotted
    capture_deps.model.track.return_value = iter([result])
    preview = object()

    with (
        patch.object(
            cr,
            "get_settings",
            return_value=_settings(
                show_video=True, show_plot=True, blur_video=True
            ),
        ),
        patch.object(cr, "_opencv_has_gui", return_value=True),
        patch.object(cr, "_blur_boxes", return_value=preview) as blur,
    ):
        cr.run_capture()

    blur.assert_called_once_with("frame", result)
    result.plot.assert_called_once_with(img=preview)
    capture_deps.cv2.imshow.assert_called_once_with(
        "Preview movimentos", plotted
    )


def test_run_capture_ComStreamOn_EscreveLiveShm(capture_deps):
    live = MagicMock()
    live.name = "live-test"
    result = _result()
    capture_deps.model.track.return_value = iter([result])
    capture_deps.cap.get.return_value = 30

    with (
        patch.object(cr, "get_settings", return_value=_settings()),
        patch.object(cr, "_open_live_shm", return_value=live),
        patch.object(cr, "export_active", return_value=True),
        patch.object(cr, "start_supervisor") as start,
    ):
        cr.run_capture()

    live.write.assert_called_once_with("frame", 30)
    start.assert_called_once_with(
        "live-test",
        clip_shm_name="vigia-onboard-clip-test",
        live_shm=live,
        capture_fps=30,
    )
    live.reset_sequence.assert_called_once()
    live.close.assert_called_once()
    live.unlink.assert_called_once()


def test_run_capture_FlagsOff_NaoEscreveLiveShm(capture_deps):
    live = MagicMock()
    live.name = "live-test"
    capture_deps.model.track.return_value = iter([_result()])

    with (
        patch.object(cr, "get_settings", return_value=_settings()),
        patch.object(cr, "_open_live_shm", return_value=live),
        patch.object(cr, "export_active", return_value=False),
    ):
        cr.run_capture()

    live.write.assert_not_called()
