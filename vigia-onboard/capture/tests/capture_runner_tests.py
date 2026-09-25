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

    model.predict.assert_called_once_with("frame", verbose=False)
    cap.release.assert_called_once()
