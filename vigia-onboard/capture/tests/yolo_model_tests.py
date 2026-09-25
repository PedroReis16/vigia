"""Testes unitários para src.yolo_model."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src import yolo_model as ym


def test_yolo_model_load_UsaExport(tmp_path):
    weights = tmp_path / "yolo26s-pose.onnx"
    weights.write_bytes(b"x")
    fake = MagicMock()

    with patch.object(ym, "get_settings", return_value=MagicMock(yolo_model="yolo26s-pose")), patch.object(
        ym, "ensure_yolo_pose_export", return_value=weights
    ) as export, patch.object(ym, "YOLO", return_value=fake) as ctor:
        loaded = ym.YoloModel.load()

    export.assert_called_once_with("yolo26s-pose")
    ctor.assert_called_once_with(str(weights))
    assert loaded.model is fake
