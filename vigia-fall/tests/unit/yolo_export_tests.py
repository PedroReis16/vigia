"""Testes unitários para shared.yolo_export."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from shared import yolo_export as ye


def test_normalize_yolo_pose_stem_ComNomeSimples_Mantem():
    assert ye.normalize_yolo_pose_stem("yolo26s-pose") == "yolo26s-pose"


def test_normalize_yolo_pose_stem_ComSufixos_Remove():
    assert ye.normalize_yolo_pose_stem("yolo26s-pose.onnx") == "yolo26s-pose"
    assert ye.normalize_yolo_pose_stem("yolo26s-pose_ncnn_model") == "yolo26s-pose"
    assert ye.normalize_yolo_pose_stem("yolo26s-pose.mlpackage") == "yolo26s-pose"


def test_normalize_yolo_pose_stem_Vazio_UsaDefault():
    assert ye.normalize_yolo_pose_stem("") == ye.DEFAULT_YOLO_POSE_STEM
    assert ye.normalize_yolo_pose_stem(None) == ye.DEFAULT_YOLO_POSE_STEM


def test_yolo_export_artifact_path_PorBackend(tmp_path: Path):
    assert ye.yolo_export_artifact_path(tmp_path, "m", "onnx") == tmp_path / "models" / "yolo" / "m.onnx"
    assert (
        ye.yolo_export_artifact_path(tmp_path, "m", "coreml")
        == tmp_path / "models" / "yolo" / "m.mlpackage"
    )
    assert (
        ye.yolo_export_artifact_path(tmp_path, "m", "ncnn")
        == tmp_path / "models" / "yolo" / "m_ncnn_model"
    )


def test_detect_yolo_export_backend_Windows():
    with patch.object(ye, "is_frozen", return_value=False), patch.object(
        ye.sys, "platform", "win32"
    ):
        assert ye.detect_yolo_export_backend() == "onnx"


def test_detect_yolo_export_backend_Darwin():
    with patch.object(ye, "is_frozen", return_value=False), patch.object(
        ye.sys, "platform", "darwin"
    ):
        assert ye.detect_yolo_export_backend() == "coreml"


def test_detect_yolo_export_backend_Linux():
    with patch.object(ye, "is_frozen", return_value=False), patch.object(
        ye.sys, "platform", "linux"
    ):
        assert ye.detect_yolo_export_backend() == "ncnn"


def test_detect_yolo_export_backend_Frozen():
    with patch.object(ye, "is_frozen", return_value=True), patch.object(
        ye.sys, "platform", "win32"
    ):
        assert ye.detect_yolo_export_backend() == "ncnn"


def test_ensure_ComArtefatoOnnxPresente_NaoExporta(tmp_path: Path):
    onnx = tmp_path / "models" / "yolo" / "yolo26s-pose.onnx"
    onnx.parent.mkdir(parents=True)
    onnx.write_bytes(b"fake-onnx")

    with patch.object(ye, "_run_ultralytics_export") as export_mock:
        result = ye.ensure_yolo_pose_export(
            "yolo26s-pose", backend="onnx", root=tmp_path
        )

    assert result == onnx.resolve()
    export_mock.assert_not_called()


def test_ensure_ComArtefatoNcnnPresente_NaoExporta(tmp_path: Path):
    ncnn = tmp_path / "models" / "yolo" / "demo_ncnn_model"
    ncnn.mkdir(parents=True)
    (ncnn / "model.ncnn.param").write_text("p")
    (ncnn / "model.ncnn.bin").write_bytes(b"b")

    with patch.object(ye, "_run_ultralytics_export") as export_mock:
        result = ye.ensure_yolo_pose_export("demo", backend="ncnn", root=tmp_path)

    assert result == ncnn.resolve()
    export_mock.assert_not_called()


def test_ensure_PathAbsolutoExistente_UsaDireto(tmp_path: Path):
    custom = tmp_path / "custom.onnx"
    custom.write_bytes(b"x")
    result = ye.ensure_yolo_pose_export(str(custom), backend="onnx", root=tmp_path)
    assert result == custom.resolve()


def test_ensure_FrozenSemArtefato_Levanta(tmp_path: Path):
    with patch.object(ye, "is_frozen", return_value=True):
        with pytest.raises(FileNotFoundError, match="bundle"):
            ye.ensure_yolo_pose_export("yolo26s-pose", backend="ncnn", root=tmp_path)


def test_ensure_SemArtefato_ExportaEMove(tmp_path: Path):
    produced_dir = tmp_path / "work"
    produced_dir.mkdir()
    produced = produced_dir / "yolo26s-pose.onnx"
    produced.write_bytes(b"exported")

    def fake_export(stem, backend, work_dir):
        dest = work_dir / f"{stem}.onnx"
        dest.write_bytes(b"exported")
        return dest

    with patch.object(ye, "is_frozen", return_value=False), patch.object(
        ye, "_run_ultralytics_export", side_effect=fake_export
    ):
        result = ye.ensure_yolo_pose_export(
            "yolo26s-pose", backend="onnx", root=tmp_path
        )

    expected = tmp_path / "models" / "yolo" / "yolo26s-pose.onnx"
    assert result == expected.resolve()
    assert expected.is_file()


def test_resolve_yolo_pose_weights_Delega(tmp_path: Path):
    onnx = tmp_path / "models" / "yolo" / "yolo26s-pose.onnx"
    onnx.parent.mkdir(parents=True)
    onnx.write_bytes(b"ok")

    with patch.object(ye, "repo_or_bundle_root", return_value=tmp_path), patch.object(
        ye, "detect_yolo_export_backend", return_value="onnx"
    ):
        path = ye.resolve_yolo_pose_weights("yolo26s-pose")

    assert path == str(onnx.resolve())
