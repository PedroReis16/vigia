"""Testes do FallDetector (máquina de estados)."""

from __future__ import annotations

from capture.models.fall_detector import FallDetector, FallDetectorConfig, FallState


def _config() -> FallDetectorConfig:
    return FallDetectorConfig(
        threshold_high=0.65,
        threshold_low=0.35,
        persistence_frames=3,
        suspect_max_frames=5,
        cooldown_frames=2,
        score_history_size=16,
    )


def test_fall_detector_normal_para_suspect_com_score_persistente() -> None:
    detector = FallDetector(_config())

    for ts in range(1, 3):
        assert detector.update(0.8, float(ts)) == FallState.NORMAL

    assert detector.update(0.8, 3.0) == FallState.SUSPECT


def test_fall_detector_suspect_para_fall_com_score_persistente() -> None:
    detector = FallDetector(_config())
    cfg = detector.config

    for ts in range(1, cfg.persistence_frames + 1):
        detector.update(cfg.threshold_high, float(ts))
    assert detector.state == FallState.SUSPECT

    for ts in range(cfg.persistence_frames + 1, 2 * cfg.persistence_frames + 1):
        state = detector.update(cfg.threshold_high, float(ts))
    assert state == FallState.FALL


def test_fall_detector_suspect_para_normal_quando_score_cai() -> None:
    detector = FallDetector(_config())
    cfg = detector.config

    for ts in range(1, cfg.persistence_frames + 1):
        detector.update(cfg.threshold_high, float(ts))
    assert detector.state == FallState.SUSPECT

    assert detector.update(cfg.threshold_low - 0.1, 10.0) == FallState.NORMAL


def test_fall_detector_suspect_para_false_positive_apos_timeout() -> None:
    detector = FallDetector(_config())
    cfg = detector.config

    for ts in range(1, cfg.persistence_frames + 1):
        detector.update(cfg.threshold_high, float(ts))
    assert detector.state == FallState.SUSPECT

    warm_score = (cfg.threshold_low + cfg.threshold_high) / 2
    for ts in range(cfg.persistence_frames + 1, cfg.persistence_frames + cfg.suspect_max_frames):
        detector.update(warm_score, float(ts))

    assert detector.update(warm_score, 100.0) == FallState.FALSE_POSITIVE


def test_fall_detector_fall_retorna_normal_apos_cooldown() -> None:
    detector = FallDetector(_config())
    cfg = detector.config

    for ts in range(1, 2 * cfg.persistence_frames + 1):
        detector.update(cfg.threshold_high, float(ts))
    assert detector.state == FallState.FALL

    for ts in range(2 * cfg.persistence_frames + 1, 2 * cfg.persistence_frames + cfg.cooldown_frames):
        detector.update(cfg.threshold_low, float(ts))

    assert detector.update(cfg.threshold_low, 100.0) == FallState.NORMAL


def test_fall_detector_resolve_suspicion_confirma_queda() -> None:
    detector = FallDetector(_config())
    cfg = detector.config

    for ts in range(1, cfg.persistence_frames + 1):
        detector.update(cfg.threshold_high, float(ts))
    assert detector.state == FallState.SUSPECT

    assert detector.resolve_suspicion(True) == FallState.FALL
    assert detector.state == FallState.FALL


def test_fall_detector_resolve_suspicion_rejeita_queda() -> None:
    detector = FallDetector(_config())
    cfg = detector.config

    for ts in range(1, cfg.persistence_frames + 1):
        detector.update(cfg.threshold_high, float(ts))
    assert detector.state == FallState.SUSPECT

    assert detector.resolve_suspicion(False) == FallState.FALSE_POSITIVE
    assert detector.state == FallState.FALSE_POSITIVE
