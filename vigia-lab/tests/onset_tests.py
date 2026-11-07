import numpy as np

from vigia_lab.onset import trunk_angle_deg, trunk_onset


def _kp(angle_deg: float, valid: bool = True) -> np.ndarray:
    kp = np.zeros((17, 3), dtype=np.float32)
    if not valid:
        return kp
    a = np.radians(angle_deg)
    hip = np.array([100.0, 200.0])
    sho = hip + 80.0 * np.array([np.sin(a), -np.cos(a)])          # 0° = ombros acima do quadril
    for j in (11, 12):
        kp[j] = (*hip, 0.9)
    for j in (5, 6):
        kp[j] = (*sho, 0.9)
    return kp


def test_angle_is_zero_upright_and_ninety_lying() -> None:
    ang = trunk_angle_deg(np.stack([_kp(0), _kp(45), _kp(90)]))
    np.testing.assert_allclose(ang, [0, 45, 90], atol=1e-3)


def test_onset_needs_two_consecutive_frames_over_threshold() -> None:
    angles = [5, 10, 70, 20, 65, 75, 85, 90]            # o pico isolado em 70° não conta
    kp = np.stack([_kp(a) for a in angles])
    t = np.arange(len(angles)) * 0.1
    assert abs(trunk_onset(t, kp) - 0.4) < 1e-9          # 65° (idx 4) + 75° (idx 5)


def test_onset_ignores_invalid_frames_and_returns_none_without_fall() -> None:
    kp = np.stack([_kp(10), _kp(0, valid=False), _kp(20)])
    assert trunk_onset(np.arange(3) * 0.1, kp) is None
    assert np.isnan(trunk_angle_deg(kp)[1])
