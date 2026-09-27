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
    ):
        yield SimpleNamespace(
            cap=cap,
            cv2=cv2,
            model=model,
        )


def test_source_label_CameraEVideo():
    assert cr._source_label(0) == "câmera 0"
    assert "clip.mp4" in cr._source_label("/tmp/clip.mp4")


def test_should_restart_stream_SoArquivoComLoopEFrames():
    assert cr._should_restart_stream("/tmp/clip.mp4", True, True, False)
    assert not cr._should_restart_stream(0, True, True, False)
    assert not cr._should_restart_stream("/tmp/clip.mp4", False, True, False)
    assert not cr._should_restart_stream("/tmp/clip.mp4", True, False, False)
    assert not cr._should_restart_stream("/tmp/clip.mp4", True, True, True)


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

    with patch.object(cr, "get_settings", return_value=_settings()):
        cr.run_capture()

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


def test_create_metadata_SemKeypoints_DevolveNone():
    assert cr._create_metadata(None) is None
    assert cr._create_metadata(SimpleNamespace(keypoints=None)) is None


def test_create_metadata_ComPessoa_IncluiBoxEKeypoints():
    sliced = MagicMock()
    sliced.tolist.return_value = [[1.0, 2.0, 0.9]]
    kpts = MagicMock()
    kpts.cpu.return_value.numpy.return_value.__getitem__.return_value = sliced
    boxes = SimpleNamespace(
        xyxy=[MagicMock(**{"tolist.return_value": [1.0, 2.0, 3.0, 4.0]})],
        conf=[0.8],
        id=[7],
    )
    result = SimpleNamespace(keypoints=SimpleNamespace(data=[kpts]), boxes=boxes)

    with patch.object(cr.time, "time", return_value=123.0):
        payload = cr._create_metadata(result)

    assert payload == {
        "ts": 123.0,
        "people": [
            {
                "id": 7,
                "box": [1.0, 2.0, 3.0, 4.0],
                "conf": 0.8,
                "keypoints": [[1.0, 2.0, 0.9]],
            }
        ],
    }


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
