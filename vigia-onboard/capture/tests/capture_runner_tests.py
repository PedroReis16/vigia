"""Testes unitários para src.capture_runner."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src import capture_runner as cr


def test_source_label_CameraEVideo():
    assert cr._source_label(0) == "câmera 0"
    assert "clip.mp4" in cr._source_label("/tmp/clip.mp4")


def test_run_capture_FonteFechada_Levanta():
    settings = SimpleNamespace(
        capture_source=0,
        show_video=False,
        show_yolo_plot=False,
        capture_loop=False,
        yolo_model="yolo26s-pose",
    )
    cap = MagicMock()
    cap.isOpened.return_value = False

    cv2 = MagicMock()
    cv2.VideoCapture.return_value = cap

    with patch.object(cr, "get_settings", return_value=settings), patch.object(
        cr, "get_yolo_model", return_value=MagicMock()
    ), patch.object(cr, "_opencv", return_value=cv2):
        with pytest.raises(ValueError, match="fonte de captura"):
            cr.run_capture()

    cap.release.assert_called_once()


def test_run_capture_UmFrame_PredizEEncerra():
    settings = SimpleNamespace(
        capture_source=0,
        show_video=False,
        show_yolo_plot=False,
        capture_loop=False,
        yolo_model="yolo26s-pose",
    )
    model = MagicMock()
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.side_effect = [(True, "frame"), (False, None)]

    cv2 = MagicMock()
    cv2.VideoCapture.return_value = cap

    with patch.object(cr, "get_settings", return_value=settings), patch.object(
        cr, "get_yolo_model", return_value=model
    ), patch.object(cr, "_opencv", return_value=cv2):
        cr.run_capture()

    model.predict.assert_called_once_with("frame", verbose=False, classes=[0])
    cap.release.assert_called_once()


def test_blur_boxes_SemDetecao_DevolveCopia():
    cv2 = MagicMock()
    image = MagicMock()
    preview = MagicMock()
    image.copy.return_value = preview

    assert cr._blur_boxes(cv2, image, []) is preview
    cv2.blur.assert_not_called()


def test_blur_boxes_AplicaNasBoxes():
    cv2 = MagicMock()
    roi = MagicMock()
    roi.size = 10
    preview = MagicMock()
    preview.shape = (100, 80, 3)
    preview.__getitem__.return_value = roi
    image = MagicMock()
    image.copy.return_value = preview
    results = [SimpleNamespace(boxes=SimpleNamespace(xyxy=[[10, 20, 40, 60]]))]

    assert cr._blur_boxes(cv2, image, results, ksize=51) is preview
    preview.__setitem__.assert_called_once()
    cv2.blur.assert_called_once_with(roi, (51, 51))


def test_run_capture_ShowVideo_BlurEPlot():
    settings = SimpleNamespace(
        capture_source=0,
        show_video=True,
        show_yolo_plot=True,
        capture_loop=False,
        yolo_model="yolo26s-pose",
    )
    plotted = object()
    result = MagicMock()
    result.plot.return_value = plotted
    model = MagicMock()
    model.predict.return_value = [result]
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.read.side_effect = [(True, "frame"), (False, None)]
    preview = object()

    cv2 = MagicMock()
    cv2.VideoCapture.return_value = cap
    cv2.waitKey.return_value = 0

    with patch.object(cr, "get_settings", return_value=settings), patch.object(
        cr, "get_yolo_model", return_value=model
    ), patch.object(cr, "_opencv", return_value=cv2), patch.object(
        cr, "_opencv_has_gui", return_value=True
    ), patch.object(
        cr, "_blur_boxes", return_value=preview
    ) as blur:
        cr.run_capture()

    blur.assert_called_once_with(cv2, "frame", [result])
    result.plot.assert_called_once_with(img=preview)
    cv2.imshow.assert_called_once_with("Preview movimentos", plotted)
