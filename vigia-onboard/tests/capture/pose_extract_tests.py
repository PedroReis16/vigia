"""Unpack de points brutos a partir do Results YOLO."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from capture.pose_extract import unpack_raw_points
from core.models.types import PoseObservation


def test_unpack_sem_keypoints_devolve_vazio():
    assert unpack_raw_points(SimpleNamespace(keypoints=None)) == []
    assert unpack_raw_points(SimpleNamespace(keypoints=SimpleNamespace(data=[]))) == []


def test_unpack_pessoa_com_id_e_kpts():
    kpts = np.ones((17, 3), dtype=np.float32)
    result = SimpleNamespace(
        keypoints=SimpleNamespace(data=[kpts]),
        boxes=SimpleNamespace(id=[9]),
    )
    observations = unpack_raw_points(result, timestamp=12.5)
    assert len(observations) == 1
    obs = observations[0]
    assert isinstance(obs, PoseObservation)
    assert obs.person_id == 9
    assert obs.timestamp == 12.5
    assert obs.keypoints.shape == (17, 3)


def test_unpack_sem_id_usa_indice():
    short = np.ones((10, 3), dtype=np.float32)
    result = SimpleNamespace(
        keypoints=SimpleNamespace(data=[short]),
        boxes=SimpleNamespace(id=None),
    )
    observations = unpack_raw_points(result, timestamp=1.0)
    assert observations[0].person_id == 0
    assert observations[0].keypoints.shape == (17, 3)
