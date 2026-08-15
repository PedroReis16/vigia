"""
Testes unitários para process_frame após integração GRU.
Verifica que o retorno é {person_id: {"raw_kpts": (51,), "timestamp": float}}.
"""

from unittest.mock import MagicMock

import numpy as np
import pytest

from capture.frame_processor import process_frame


def _tensor_mock(array: np.ndarray) -> MagicMock:
    """Emula um tensor PyTorch: tem .numpy() que retorna o ndarray."""
    t = MagicMock()
    t.numpy.return_value = array
    return t


def _mock_track_result(n_persons: int = 1, conf_value: float = 0.9):
    """Monta resultado fake do YOLO com n_persons pessoas."""
    kpts_tensors = []
    for _ in range(n_persons):
        kp = np.random.rand(17, 3).astype(np.float32)
        kp[:, 2] = conf_value
        kpts_tensors.append(_tensor_mock(kp))

    kpts = MagicMock()
    kpts.data = kpts_tensors
    result = MagicMock()
    result.keypoints = kpts
    result.boxes.id = None
    return [result]


def test_process_frame_ComPessoaDetectada_RetornaRawKptsFormat(monkeypatch):
    modelo = MagicMock()
    modelo.track.return_value = _mock_track_result(n_persons=1)
    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)
    monkeypatch.setattr(
        "capture.frame_processor.get_person_runtime_store",
        lambda: MagicMock(cleanup=lambda ids: None),
    )

    result = process_frame(np.zeros((480, 640, 3), dtype=np.uint8), capture_date=0.0)

    assert result is not None
    assert len(result) == 1
    person_data = list(result.values())[0]
    assert "raw_kpts" in person_data
    assert person_data["raw_kpts"].shape == (51,)
    assert "timestamp" in person_data
    assert person_data["timestamp"] == 0.0


def test_process_frame_ComJointsBaixaConfianca_ZeraKeypoints(monkeypatch):
    modelo = MagicMock()
    kp = np.ones((17, 3), dtype=np.float32)
    kp[:, 2] = 0.1  # conf < 0.25 → deve ser zerado
    result_mock = MagicMock()
    result_mock.keypoints.data = [_tensor_mock(kp)]
    result_mock.boxes.id = None
    modelo.track.return_value = [result_mock]
    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)
    monkeypatch.setattr(
        "capture.frame_processor.get_person_runtime_store",
        lambda: MagicMock(cleanup=lambda ids: None),
    )

    result = process_frame(np.zeros((480, 640, 3), dtype=np.uint8), capture_date=1.0)

    kpts = list(result.values())[0]["raw_kpts"]
    assert np.all(kpts == 0)


def test_process_frame_ComJointsAltaConfianca_MantemValores(monkeypatch):
    modelo = MagicMock()
    kp = np.ones((17, 3), dtype=np.float32) * 0.5
    kp[:, 2] = 0.9  # conf > 0.25 → mantém
    result_mock = MagicMock()
    result_mock.keypoints.data = [_tensor_mock(kp)]
    result_mock.boxes.id = None
    modelo.track.return_value = [result_mock]
    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)
    monkeypatch.setattr(
        "capture.frame_processor.get_person_runtime_store",
        lambda: MagicMock(cleanup=lambda ids: None),
    )

    result = process_frame(np.zeros((480, 640, 3), dtype=np.uint8), capture_date=2.0)

    kpts = list(result.values())[0]["raw_kpts"]
    assert not np.all(kpts == 0)


def test_process_frame_SemDeteccoes_RetornaNone(monkeypatch):
    modelo = MagicMock()
    modelo.track.return_value = []
    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)

    result = process_frame(np.zeros((8, 8, 3), dtype=np.uint8), capture_date=0.0)

    assert result is None
