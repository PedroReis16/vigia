"""Testes unitários para capture.frame_processor.extract_poses."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from capture.frame_processor import extract_poses


def test_extract_poses_sem_deteccoes_retorna_lista_vazia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modelo = MagicMock()
    modelo.track.return_value = []
    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)
    monkeypatch.setattr(
        "capture.frame_processor.get_person_runtime_store",
        lambda: MagicMock(cleanup=MagicMock()),
    )

    result = extract_poses(np.zeros((8, 8, 3), dtype=np.uint8), 1.0)

    assert result == []
    modelo.track.assert_called_once()


def test_extract_poses_com_pessoa_retorna_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kpts_data = MagicMock()
    person = MagicMock()
    person.numpy.return_value = np.ones((17, 3), dtype=np.float32)
    kpts_data.data = [person]
    kpts_data.__len__ = lambda self: 1

    boxes = MagicMock()
    boxes.id = None

    result = MagicMock()
    result.keypoints = kpts_data
    result.boxes = boxes

    modelo = MagicMock()
    modelo.track.return_value = [result]
    cleanup = MagicMock()
    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)
    monkeypatch.setattr(
        "capture.frame_processor.get_person_runtime_store",
        lambda: MagicMock(cleanup=cleanup),
    )

    observations = extract_poses(np.zeros((8, 8, 3), dtype=np.uint8), 2.5)

    assert len(observations) == 1
    assert observations[0].person_id == 0
    assert observations[0].keypoints.shape == (17, 3)
    assert observations[0].timestamp == 2.5
    cleanup.assert_called_once()


def test_extract_poses_com_excecao_propaga_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    modelo = MagicMock()
    modelo.track.side_effect = RuntimeError("falha no yolo")
    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)

    with pytest.raises(RuntimeError, match="Erro ao processar o frame"):
        extract_poses(np.zeros((8, 8, 3), dtype=np.uint8), 1.0)
